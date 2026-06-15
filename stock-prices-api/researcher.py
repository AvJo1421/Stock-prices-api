import asyncio
import json
import os
from typing import TypedDict, Optional
from dotenv import load_dotenv
import websockets
import pandas as pd
import chromadb
import speech_recognition as sr
import pyttsx3
from langgraph.graph import StateGraph, START, END
from langchain_anthropic import ChatAnthropic

load_dotenv()

API_KEY = os.getenv("POLYGON_API_KEY")
llm = ChatAnthropic(model="claude-sonnet-4-6")

# --- ChromaDB setup ---
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(name="stock_data")

# --- Voice helpers ---
def listen():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        audio = recognizer.listen(source)
    try:
        text = recognizer.recognize_google(audio)
        print(f"You said: {text}")
        return text
    except sr.UnknownValueError:
        print("Could not understand audio")
        return None
    except sr.RequestError:
        print("Speech recognition service unavailable")
        return None

def speak(text):
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()

# --- State ---
class ResearcherState(TypedDict):
    ticker: str
    live_price: Optional[float]
    historical_data: Optional[list]
    question: str
    answer: Optional[str]

# --- Nodes ---
def query_chroma(state: ResearcherState) -> ResearcherState:
    ticker = state["ticker"]
    question = state["question"]

    results = collection.query(
        query_texts=[question],
        n_results=5,
        where={"ticker": ticker}
    )

    state["historical_data"] = results["documents"][0]
    return state

async def fetch_live_price(state: ResearcherState) -> ResearcherState:
    ticker = state["ticker"]
    url = "wss://delayed.polygon.io/stocks"

    try:
        async with websockets.connect(url) as ws:
            await ws.send(json.dumps({"action": "auth", "params": API_KEY}))
            await ws.recv()

            await ws.send(json.dumps({"action": "subscribe", "params": f"A.{ticker}"}))
            await ws.recv()

            try:
                while True:
                    msg = await asyncio.wait_for(ws.recv(), timeout=5)
                    data = json.loads(msg)
                    for item in data:
                        if item.get("ev") == "A" and item.get("sym") == ticker:
                            state["live_price"] = item["c"]
                            return state
            except asyncio.TimeoutError:
                print("Market closed — using ChromaDB data only")
                state["live_price"] = None
                return state

    except Exception as e:
        print(f"WebSocket error: {e}")
        state["live_price"] = None
        return state

def generate_answer(state: ResearcherState) -> ResearcherState:
    question = state["question"]
    ticker = state["ticker"]
    live_price = state["live_price"]
    historical_data = state["historical_data"]

    prompt = f"""
    You are a stock research assistant.
    
    The user asked: {question}
    
    Here is the data for {ticker}:
    - Current live price: ${live_price}
    - Relevant historical data: {historical_data}
    
    Answer the user's question clearly and concisely based on this data.
    """

    response = llm.invoke(prompt)
    state["answer"] = response.content
    return state

# --- Graph ---
builder = StateGraph(ResearcherState)
builder.add_node("query_chroma", query_chroma)
builder.add_node("fetch_live_price", fetch_live_price)
builder.add_node("generate_answer", generate_answer)
builder.add_edge(START, "query_chroma")
builder.add_edge("query_chroma", "fetch_live_price")
builder.add_edge("fetch_live_price", "generate_answer")
builder.add_edge("generate_answer", END)
graph = builder.compile()

# --- Run ---
async def main():
    ticker = input("Enter ticker: ").upper()
    print(f"Researching {ticker} — say 'done' to exit\n")

    while True:
        print("Ask your question...")
        question = listen()

        if not question:
            print("Could not hear — try again")
            continue

        if question.lower() in ["done", "exit", "quit", "stop"]:
            speak("Goodbye!")
            print("Goodbye!")
            break

        result = await graph.ainvoke({
            "ticker": ticker,
            "live_price": None,
            "historical_data": None,
            "question": question,
            "answer": None
        })

        print(f"\nQuestion: {result['question']}")
        print(f"\nAnswer: {result['answer']}\n")

        speak(result["answer"])

asyncio.run(main())
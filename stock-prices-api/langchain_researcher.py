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
from langchain_anthropic import ChatAnthropic
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
from langgraph.graph import StateGraph, START, END

load_dotenv()

API_KEY = os.getenv("POLYGON_API_KEY")
llm = ChatAnthropic(model="claude-sonnet-4-6", temperature=0)

# --- Load dataframe ---
df = pd.read_parquet("data_clean.parquet")

# --- ChromaDB news setup ---
news_client = chromadb.PersistentClient(path="./chroma_news")
news_collection = news_client.get_or_create_collection(name="stock_news")

# --- Voice helpers ---
def listen():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        print("Listening...")
        audio = recognizer.listen(source, phrase_time_limit=15)
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
    ticker: Optional[str]
    question: str
    live_price: Optional[float]
    historical_data: Optional[str]
    answer: Optional[str]
    chat_history: list

# --- Nodes ---
def fetch_news_context(state: ResearcherState) -> ResearcherState:
    question = state["question"]

    results = news_collection.query(
        query_texts=[question],
        n_results=3
    )

    articles = results["documents"][0]
    state["historical_data"] = "\n\n---\n\n".join(articles)
    return state

async def fetch_live_price(state: ResearcherState) -> ResearcherState:
    ticker = state["ticker"]

    if not ticker:
        state["live_price"] = None
        return state

    url = "wss://delayed.polygon.io/stocks"

    try:
        async with websockets.connect(url) as ws:
            await ws.send(json.dumps({"action": "auth", "params": API_KEY}))
            await ws.recv()

            await ws.send(json.dumps({"action": "subscribe", "params": f"A.{ticker}"}))
            await ws.recv()

            try:
                while True:
                    msg = await asyncio.wait_for(ws.recv(), timeout=3)
                    data = json.loads(msg)
                    for item in data:
                        if item.get("ev") == "A" and item.get("sym") == ticker:
                            state["live_price"] = item["c"]
                            return state
            except asyncio.TimeoutError:
                print("Market closed — using dataframe only")
                state["live_price"] = None
                return state

    except Exception as e:
        print(f"WebSocket error: {e}")
        state["live_price"] = None
        return state

def generate_answer(state: ResearcherState) -> ResearcherState:
    question = state["question"]
    live_price = state["live_price"]
    chat_history = state["chat_history"]
    news_context = state["historical_data"]

    if chat_history:
        history_text = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in chat_history[-4:]])
        question = f"Previous conversation:\n{history_text}\n\nNew question: {question}"

    if live_price:
        question = f"{question} (current live price is ${live_price})"

    if news_context:
        question = f"{question}\n\nRelevant news:\n{news_context}"

    agent = create_pandas_dataframe_agent(
        llm,
        df,
        verbose=True,
        allow_dangerous_code=True,
        handle_parsing_errors=True,
        agent_executor_kwargs={"handle_parsing_errors": True},
        prefix="You are a stock research assistant. Answer only what is asked. Do not give numbers if not asked for. Keep answers as short as possible. Be direct and concise. No extra context, no suggestions, no markdown. If news articles are provided, use them to explain price movements."
    )

    try:
        result = agent.invoke(question)
        state["answer"] = result["output"]
    except Exception as e:
        state["answer"] = "I could not understand that question. Please try again."

    return state

# --- Graph ---
builder = StateGraph(ResearcherState)
builder.add_node("fetch_news_context", fetch_news_context)
builder.add_node("fetch_live_price", fetch_live_price)
builder.add_node("generate_answer", generate_answer)
builder.add_edge(START, "fetch_news_context")
builder.add_edge("fetch_news_context", "fetch_live_price")
builder.add_edge("fetch_live_price", "generate_answer")
builder.add_edge("generate_answer", END)
graph = builder.compile()

# --- Run ---
async def main():
    print("StockFlow Researcher — say 'done' to exit\n")
    chat_history = []

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
            "ticker": None,
            "question": question,
            "live_price": None,
            "historical_data": None,
            "answer": None,
            "chat_history": chat_history
        })

        print(f"\nQuestion: {result['question']}")
        print(f"\nAnswer: {result['answer']}\n")

        chat_history.append({"role": "user", "content": question})
        chat_history.append({"role": "assistant", "content": result["answer"]})

        speak(result["answer"])

asyncio.run(main())
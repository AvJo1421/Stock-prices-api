import os
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv
import pandas as pd
import chromadb
from langchain_anthropic import ChatAnthropic
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent

from google.cloud import storage
import os

def download_from_gcs():
    client = storage.Client()
    bucket = client.bucket("stockflow-data")

    # Download parquet
    if not os.path.exists("data_clean.parquet"):
        bucket.blob("data_clean.parquet").download_to_filename("data_clean.parquet")
        print("Downloaded data_clean.parquet")

    # Download chroma_news
    if not os.path.exists("chroma_news"):
        blobs = client.list_blobs("stockflow-data", prefix="chroma_news/")
        for blob in blobs:
            local_path = blob.name
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            blob.download_to_filename(local_path)
        print("Downloaded chroma_news")

download_from_gcs()

load_dotenv()

app = FastAPI()

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://stockflow-deployment.web.app"
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

llm = ChatAnthropic(model="claude-sonnet-4-6", temperature=0)

# --- Load data ---
df = pd.read_parquet("data_clean.parquet")
news_client = chromadb.PersistentClient(path="./chroma_news")
news_collection = news_client.get_or_create_collection(name="stock_news")

# --- Request model ---
class ResearchRequest(BaseModel):
    question: str
    ticker: Optional[str] = None

# --- Endpoint ---
@app.post("/research")
def research(request: ResearchRequest):
    question = request.question
    ticker = request.ticker

    # Fetch relevant news
    news_results = news_collection.query(
        query_texts=[question],
        n_results=3
    )
    news_context = "\n\n---\n\n".join(news_results["documents"][0])

    # Filter dataframe if ticker provided
    target_df = df[df["ticker"] == ticker].copy() if ticker else df

    # Build full question
    full_question = question
    if news_context:
        full_question = f"{question}\n\nRelevant news:\n{news_context}"

    # Run pandas agent
    agent = create_pandas_dataframe_agent(
        llm,
        target_df,
        verbose=True,
        allow_dangerous_code=True,
        handle_parsing_errors=True,
        agent_executor_kwargs={"handle_parsing_errors": True},
        prefix="You are a stock research assistant. Answer only what is asked. Be direct and concise. No extra context, no suggestions, no markdown. If news articles are provided, use them to explain price movements."
    )

    try:
        result = agent.invoke(full_question)
        answer = result["output"]
    except Exception:
        answer = "Could not process that question. Please try again."

    return {
        "question": question,
        "answer": answer
    }

@app.get("/health")
def health():
    return {"status": "ok"}


from anthropic import Anthropic

anthropic_client = Anthropic()

class PodcastRequest(BaseModel):
    topic: str
    duration_minutes: int = 5

@app.post("/podcast")
def podcast(request: PodcastRequest):
    topic = request.topic
    duration_minutes = request.duration_minutes
    turns = duration_minutes * 2  # roughly 2 turns per minute

    # Get relevant data
    news_results = news_collection.query(
        query_texts=[topic],
        n_results=5
    )
    news_context = "\n\n".join(news_results["documents"][0])

    # Data summary
    data_summary = df.groupby("ticker").agg(
        latest_close=("close", "last"),
        return_pct=("close", lambda x: round((x.iloc[-1] - x.iloc[0]) / x.iloc[0] * 100, 2))
    ).to_string()

    conversation = []
    history = []

    host_system = f"""You are a professional financial podcast host named Sarah. 
    You are discussing: {topic}
    Keep responses to  1-2 sentences Natural, engaging tone. Have some voice modulations when speaking. Start with a short 1 line intro
     and keep questions very concise.  Ask the analyst specific questions.
    Never use markdown, asterisks, dashes, or bullet points. Plain conversational speech only.
    Speak naturally like a real podcast. Warm, engaging, human tone. Short punchy sentences.
    Use this data context: {data_summary}
    News context: {news_context}"""

    analyst_system = f"""You are a sharp financial analyst named James.
    You are being interviewed about: {topic}
    Keep responses to 2-3 sentences. Give numbers only when specifically asked. Have voice modulation while
     speaking. Data-driven, confident tone. Answer the host's questions directly.
    Never use markdown, asterisks, dashes, or bullet points. Plain conversational speech only. 
    Speak naturally like a real podcast. Warm, engaging, human tone. Short punchy sentences.
    Use this data context: {data_summary}
    News context: {news_context}"""

    # Opening from host
    opening = anthropic_client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=150,
        system=host_system,
        messages=[{"role": "user", "content": f"Open the podcast about {topic} with an engaging intro and first question for your analyst."}]
    )
    host_text = opening.content[0].text
    conversation.append({"speaker": "Host", "text": host_text})
    history.append({"role": "assistant", "content": host_text})

    # Back and forth
    for i in range(turns - 1):
        if i % 2 == 0:
            # Analyst responds
            response = anthropic_client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=150,
                system=analyst_system,
                messages=history + [{"role": "user", "content": conversation[-1]["text"]}]
            )
            text = response.content[0].text
            conversation.append({"speaker": "Analyst", "text": text})
        else:
            # Host follows up
            response = anthropic_client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=150,
                system=host_system,
                messages=history + [{"role": "user", "content": conversation[-1]["text"]}]
            )
            text = response.content[0].text
            conversation.append({"speaker": "Host", "text": text})

        history.append({"role": "user", "content": conversation[-2]["text"]})
        history.append({"role": "assistant", "content": text})

    # Closing
    closing = anthropic_client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=100,
        system=host_system,
        messages=history + [{"role": "user", "content": "Wrap up the podcast naturally in 1-2 sentences."}]
    )
    conversation.append({"speaker": "Host", "text": closing.content[0].text})

    return {"conversation": conversation}
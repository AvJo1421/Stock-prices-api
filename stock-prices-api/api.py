import os
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv
import pandas as pd
import chromadb
import requests
import base64
from langchain_anthropic import ChatAnthropic
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent

from google.cloud import storage
import os

import threading
import time

load_dotenv()
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")
app = FastAPI()

last_refresh_check = 0
REFRESH_CHECK_INTERVAL = 3600  # check every hour

def download_from_gcs(force=False):
    global df
    client = storage.Client()
    bucket = client.bucket("stockflow-data")

    parquet_blob = bucket.blob("data_clean.parquet")
    parquet_blob.reload()  # fetch latest metadata
    remote_updated = parquet_blob.updated.timestamp()

    local_exists = os.path.exists("data_clean.parquet")
    local_updated = os.path.getmtime("data_clean.parquet") if local_exists else 0

    if force or not local_exists or remote_updated > local_updated:
        parquet_blob.download_to_filename("data_clean.parquet")
        print(f"Downloaded fresh data_clean.parquet (updated: {parquet_blob.updated})")
        df = pd.read_parquet("data_clean.parquet")
    
    # Same check for chroma_news folder
    if not os.path.exists("chroma_news"):
        blobs = client.list_blobs("stockflow-data", prefix="chroma_news/")
        for blob in blobs:
            local_path = blob.name
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            blob.download_to_filename(local_path)
        print("Downloaded chroma_news")


def background_refresh_checker():
    while True:
        time.sleep(REFRESH_CHECK_INTERVAL)
        try:
            download_from_gcs()
        except Exception as e:
            print(f"Background refresh check failed: {e}")


download_from_gcs()

# Start background thread to check for updates every hour
refresh_thread = threading.Thread(target=background_refresh_checker, daemon=True)
refresh_thread.start()



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
    chat_history: list = []

# --- Endpoint ---
@app.post("/research")
def research(request: ResearchRequest):
    question = request.question
    ticker = request.ticker
    chat_history = request.chat_history

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
    if chat_history:
        history_text = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in chat_history[-6:]])
        full_question = f"Previous conversation:\n{history_text}\n\nNew question: {question}"

    if news_context:
        full_question = f"{full_question}\n\nRelevant news:\n{news_context}"

    # Run pandas agent
    agent = create_pandas_dataframe_agent(
        llm,
        target_df,
        verbose=True,
        allow_dangerous_code=True,
        handle_parsing_errors=True,
        agent_executor_kwargs={"handle_parsing_errors": True},
        prefix="You are a stock research assistant. Answer only what is asked. Be direct and concise. No extra context, no suggestions, no markdown. If news articles are provided, use them to explain price movements. For the first question in a conversation, answer in 1 line maximum. For follow-up questions, you may give more detail only if the user's question implies they want depth (e.g. asking 'why' or 'explain'). Never ramble or repeat information already given."
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
    turns = duration_minutes * 2

    news_results = news_collection.query(query_texts=[topic], n_results=5)
    news_context = "\n\n".join(news_results["documents"][0])

    data_summary = df.groupby("ticker").agg(
        latest_close=("close", "last"),
        return_pct=("close", lambda x: round((x.iloc[-1] - x.iloc[0]) / x.iloc[0] * 100, 2))
    ).to_string()

    conversation = []
    history = []

    host_system = f"""You are a professional financial podcast host named Sarah. 
    You are discussing: {topic}
    Keep responses to 1-2 sentences. Natural, engaging tone. Start with a short 1 line intro and keep questions very concise. Ask the analyst specific questions.
    Never use markdown, asterisks, dashes, or bullet points. Plain conversational speech only.
    Use this data context: {data_summary}
    News context: {news_context}"""

    analyst_system = f"""You are a sharp financial analyst named James.
    You are being interviewed about: {topic}
    Keep responses to 2-3 sentences. Give numbers only when specifically asked. Data-driven, confident tone.
    Never use markdown, asterisks, dashes, or bullet points. Plain conversational speech only.
    Use this data context: {data_summary}
    News context: {news_context}"""

    def add_turn(speaker, text, voice_id):
        audio_bytes = text_to_speech(text, voice_id)
        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8") if audio_bytes else None
        conversation.append({"speaker": speaker, "text": text, "audio": audio_b64})

    opening = anthropic_client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=150,
        system=host_system,
        messages=[{"role": "user", "content": f"Open the podcast about {topic} with an engaging intro and first question for your analyst."}]
    )
    host_text = opening.content[0].text
    add_turn("Host", host_text, HOST_VOICE_ID)
    history.append({"role": "assistant", "content": host_text})

    for i in range(turns - 1):
        if i % 2 == 0:
            response = anthropic_client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=150,
                system=analyst_system,
                messages=history + [{"role": "user", "content": conversation[-1]["text"]}]
            )
            text = response.content[0].text
            add_turn("Analyst", text, ANALYST_VOICE_ID)
        else:
            response = anthropic_client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=150,
                system=host_system,
                messages=history + [{"role": "user", "content": conversation[-1]["text"]}]
            )
            text = response.content[0].text
            add_turn("Host", text, HOST_VOICE_ID)

        history.append({"role": "user", "content": conversation[-2]["text"]})
        history.append({"role": "assistant", "content": text})

    closing = anthropic_client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=100,
        system=host_system,
        messages=history + [{"role": "user", "content": "Wrap up the podcast naturally in 1-2 sentences."}]
    )
    add_turn("Host", closing.content[0].text, HOST_VOICE_ID)

    return {"conversation": conversation}



TICKER_NAMES = {
    "HSBC": "HSBC Holdings", "BCS": "Barclays", "LYG": "Lloyds Banking Group",
    "NWG": "NatWest Group", "DB": "Deutsche Bank", "SAN": "Banco Santander",
    "PRU": "Prudential", "MET": "MetLife", "ALL": "Allstate",
    "TRV": "Travelers Companies", "CB": "Chubb", "AIG": "American International Group",
    "BP": "BP", "SHEL": "Shell", "TTE": "TotalEnergies",
    "E": "Eni", "XOM": "ExxonMobil", "CVX": "Chevron",
    "AZN": "AstraZeneca", "GSK": "GSK", "NVO": "Novo Nordisk",
    "SNY": "Sanofi", "JNJ": "Johnson & Johnson", "PFE": "Pfizer",
    "UL": "Unilever", "DEO": "Diageo", "BTI": "British American Tobacco",
    "PG": "Procter & Gamble", "KO": "Coca-Cola", "PEP": "PepsiCo",
    "AAPL": "Apple", "MSFT": "Microsoft", "NVDA": "NVIDIA",
    "ARM": "Arm Holdings", "GOOGL": "Alphabet", "META": "Meta Platforms",
    "VOD": "Vodafone", "T": "AT&T", "VZ": "Verizon",
    "TMUS": "T-Mobile US", "ERIC": "Ericsson", "NOK": "Nokia",
    "RIO": "Rio Tinto", "BHP": "BHP Group", "VALE": "Vale",
    "FCX": "Freeport-McMoRan", "NEM": "Newmont", "AA": "Alcoa"
}

from concurrent.futures import ThreadPoolExecutor, as_completed

def fetch_live_price(ticker):
    try:
        response = requests.get(
            f"https://api.polygon.io/v2/aggs/ticker/{ticker}/prev",
            params={"adjusted": "true", "apiKey": POLYGON_API_KEY},
            timeout=5
        )
        data = response.json()
        results = data.get("results", [])
        if results:
            return ticker, results[0]["c"]
    except Exception:
        pass
    return ticker, None

@app.get("/watchlist")
def get_watchlist():
    tickers = list(TICKER_NAMES.keys())
    live_prices = {}

    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(fetch_live_price, t) for t in tickers]
        for future in as_completed(futures):
            ticker, price = future.result()
            if price:
                live_prices[ticker] = price

    latest = df.sort_values("timestamp").groupby("ticker").last().reset_index()
    latest["name"] = latest["ticker"].map(TICKER_NAMES)

    previous = df.sort_values("timestamp").groupby("ticker").nth(-2).reset_index()
    previous_prices = previous.set_index("ticker")["close"].to_dict()

    result = []
    for _, row in latest.iterrows():
        ticker = row["ticker"]
        current_price = live_prices.get(ticker, row["close"])
        prev_price = previous_prices.get(ticker, current_price)
        change_pct = round((current_price - prev_price) / prev_price * 100, 2) if prev_price else 0

        result.append({
            "ticker": ticker,
            "name": row["name"],
            "sector": row["sector"],
            "close": current_price,
            "change_pct": change_pct,
            "timestamp": str(row["timestamp"])
        })

    return {"data": result, "fetched_at": pd.Timestamp.now(tz="Europe/London").isoformat()}
@app.get("/news")
def get_news():
    all_items = news_collection.get(include=["metadatas"])
    
    # Group by ticker, take 1-2 most recent per ticker
    from collections import defaultdict
    by_ticker = defaultdict(list)
    
    for metadata in all_items["metadatas"]:
        by_ticker[metadata.get("ticker")].append(metadata)
    
    news_items = []
    for ticker, articles in by_ticker.items():
        articles.sort(key=lambda x: x["published_utc"], reverse=True)
        news_items.extend(articles[:1])  # 1 most recent per ticker
    
    news_items.sort(key=lambda x: x["published_utc"], reverse=True)
    
    return {"news": news_items[:30]}


ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

HOST_VOICE_ID = "aD6riP1btT197c6dACmy"
ANALYST_VOICE_ID = "UgBBYS2sOqTuMpoF3BR0"

def text_to_speech(text, voice_id):
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75
        }
    }
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        return response.content  # raw audio bytes (mp3)
    return None
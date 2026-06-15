import os
import requests
import chromadb
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

API_KEY = os.getenv("POLYGON_API_KEY")

TICKERS = [
    "HSBC", "BCS", "LYG", "NWG", "DB", "SAN",
    "PRU", "MET", "ALL", "TRV", "CB", "AIG",
    "BP", "SHEL", "TTE", "E", "XOM", "CVX",
    "AZN", "GSK", "NVO", "SNY", "JNJ", "PFE",
    "UL", "DEO", "BTI", "PG", "KO", "PEP",
    "AAPL", "MSFT", "NVDA", "ARM", "GOOGL", "META",
    "VOD", "T", "VZ", "TMUS", "ERIC", "NOK",
    "RIO", "BHP", "VALE", "FCX", "NEM", "AA"
]

# --- ChromaDB setup ---
client = chromadb.PersistentClient(path="./chroma_news")

try:
    client.delete_collection(name="stock_news")
    print("Old news collection deleted")
except:
    pass

collection = client.create_collection(name="stock_news")

# --- Fetch and store news ---
documents = []
metadatas = []
ids = []
seen_ids = set()

for ticker in TICKERS:
    response = requests.get(
        "https://api.polygon.io/v2/reference/news",
        params={
            "ticker": ticker,
            "limit": 100,
            "apiKey": API_KEY
        }
    )

    if response.status_code != 200:
        print(f"❌ {ticker}: failed ({response.status_code})")
        continue

    articles = response.json().get("results", [])

    for article in articles:
        article_id = article["id"]

        if article_id in seen_ids:
            continue
        seen_ids.add(article_id)

        # Get sentiment for this ticker
        sentiment = ""
        for insight in article.get("insights", []):
            if insight["ticker"] == ticker:
                sentiment = insight.get("sentiment_reasoning", "")
                break

        doc = f"""
        Title: {article['title']}
        Published: {article['published_utc']}
        Tickers: {', '.join(article['tickers'])}
        Summary: {article.get('description','no description')}
        Sentiment for {ticker}: {sentiment}
        """

        documents.append(doc)
        metadatas.append({
            "ticker": ticker,
            "published_utc": article["published_utc"],
            "title": article["title"]
        })
        ids.append(article_id)

    print(f"✅ {ticker}: {len(articles)} articles")

# --- Store in ChromaDB ---
if documents:
    collection.add(
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )

print(f"\nDone! {len(documents)} articles stored in ChromaDB")
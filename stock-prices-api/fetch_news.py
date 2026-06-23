import os
import requests
import chromadb
from dotenv import load_dotenv
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys

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


def fetch_ticker_news(ticker, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = requests.get(
                "https://api.polygon.io/v2/reference/news",
                params={"ticker": ticker, "limit": 100, "apiKey": API_KEY},
                timeout=15
            )
            if response.status_code == 200:
                articles = response.json().get("results", [])
                print(f"✅ {ticker}: {len(articles)} articles")
                return ticker, articles
            elif attempt == max_retries - 1:
                print(f"❌ {ticker}: failed ({response.status_code})")
                return ticker, []
        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                print(f"❌ {ticker}: connection error - {e}")
                return ticker, []
    return ticker, []


# --- Fetch all tickers in parallel ---
ticker_articles = {}
failed_tickers = []

with ThreadPoolExecutor(max_workers=10) as executor:
    futures = {executor.submit(fetch_ticker_news, ticker): ticker for ticker in TICKERS}
    for future in as_completed(futures):
        ticker, articles = future.result()
        ticker_articles[ticker] = articles
        if not articles:
            failed_tickers.append(ticker)

# --- Validation ---
successful_tickers = len(TICKERS) - len(failed_tickers)
print(f"\n📊 Fetched news for {successful_tickers}/{len(TICKERS)} tickers")

if failed_tickers:
    print(f"⚠️  Failed tickers: {failed_tickers}")

total_articles = sum(len(articles) for articles in ticker_articles.values())
if total_articles == 0:
    print("❌ CRITICAL: No articles fetched at all. Aborting.")
    sys.exit(1)

if successful_tickers < len(TICKERS) * 0.7:
    print("❌ CRITICAL: Less than 70% of tickers fetched news successfully. Aborting.")
    sys.exit(1)

# --- ChromaDB setup ---
client = chromadb.PersistentClient(path="./chroma_news")

try:
    client.delete_collection(name="stock_news")
    print("Old news collection deleted")
except Exception:
    pass

collection = client.create_collection(name="stock_news")

# --- Process and store ---
documents = []
metadatas = []
ids = []
seen_ids = set()

for ticker, articles in ticker_articles.items():
    for article in articles:
        article_id = article["id"]

        if article_id in seen_ids:
            continue
        seen_ids.add(article_id)

        sentiment = ""
        for insight in article.get("insights", []):
            if insight["ticker"] == ticker:
                sentiment = insight.get("sentiment_reasoning", "")
                break

        doc = f"""
        Title: {article['title']}
        Published: {article['published_utc']}
        Tickers: {', '.join(article['tickers'])}
        Summary: {article.get('description', 'No description available')}
        Sentiment for {ticker}: {sentiment}
        """

        documents.append(doc)
        metadatas.append({
            "ticker": ticker,
            "published_utc": article["published_utc"],
            "title": article["title"]
        })
        ids.append(article_id)

if documents:
    batch_size = 5000
    for i in range(0, len(documents), batch_size):
        collection.add(
            documents=documents[i:i+batch_size],
            metadatas=metadatas[i:i+batch_size],
            ids=ids[i:i+batch_size]
        )
        print(f"Loaded {min(i+batch_size, len(documents))} / {len(documents)} articles")

print(f"\n✅ Done! {len(documents)} articles stored in ChromaDB")
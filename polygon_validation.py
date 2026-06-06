import os
import requests
import time
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("POLYGON_API_KEY")

tickers = [
    "HSBC", "BCS", "LYG", "NWG", "CS", "DB",
    "AV", "PRU", "MET",
    "BP", "SHEL", "TTE", "E",
    "AZN", "GSK", "NVO", "SNY",
    "UL", "DEO", "BTI",
    "AAPL", "MSFT", "NVDA", "ARM",
    "VOD", "BT",
    "RIO", "BHP",
    "SAN"
]

valid = []
invalid = []

for ticker in tickers:
    url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/day/2025-01-01/2025-01-31"
    params = {"adjusted": "true", "limit": 5, "apiKey": API_KEY}
    response = requests.get(url, params=params, timeout=30)
    data = response.json()
    results = data.get("results", [])

    if results:
        valid.append(ticker)
        print(f"✅ {ticker}")
    else:
        invalid.append(ticker)
        print(f"❌ {ticker}")

print(f"\n✅ Valid tickers ({len(valid)}): {valid}")
print(f"❌ Invalid tickers ({len(invalid)}): {invalid}")
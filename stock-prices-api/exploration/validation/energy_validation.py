import os
import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("POLYGON_API_KEY")

candidates = {
    "XOM":  "Energy",   # ExxonMobil
    "CVX":  "Energy",   # Chevron
    "COP":  "Energy",   # ConocoPhillips
    "ENB":  "Energy",   # Enbridge
    "SLB":  "Energy",   # Schlumberger
}

for ticker, sector in candidates.items():
    url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/day/2025-01-01/2025-01-31"
    params = {"adjusted": "true", "limit": 5, "apiKey": API_KEY}
    response = requests.get(url, params=params, timeout=30)
    results = response.json().get("results", [])
    print(f"{'✅' if results else '❌'} {ticker} ({sector})")
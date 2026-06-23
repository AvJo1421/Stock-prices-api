import os
import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("POLYGON_API_KEY")

candidates = {
    # Pharma (need 2 more)
    "JNJ":  "Pharma",    # Johnson & Johnson
    "PFE":  "Pharma",    # Pfizer
    "MRK":  "Pharma",    # Merck
    "ABBV": "Pharma",    # AbbVie
    "ROG":  "Pharma",    # Roche

    # Tech (need 2 more)
    "GOOGL":"Tech",      # Alphabet
    "META": "Tech",      # Meta
    "TSLA": "Tech",      # Tesla
    "AMZN": "Tech",      # Amazon
    "ORCL": "Tech",      # Oracle

    # Consumer (need 3 more)
    "PG":   "Consumer",  # Procter & Gamble
    "KO":   "Consumer",  # Coca-Cola
    "PEP":  "Consumer",  # PepsiCo
    "NESN": "Consumer",  # Nestle
    "CL":   "Consumer",  # Colgate
    "RB":   "Consumer",  # Reckitt
}

valid = []
invalid = []

for ticker, sector in candidates.items():
    url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/day/2025-01-01/2025-01-31"
    params = {"adjusted": "true", "limit": 5, "apiKey": API_KEY}
    response = requests.get(url, params=params, timeout=30)
    data = response.json()
    results = data.get("results", [])

    if results:
        valid.append((ticker, sector))
        print(f"✅ {ticker} ({sector})")
    else:
        invalid.append(ticker)
        print(f"❌ {ticker}")

print(f"\n✅ Valid ({len(valid)}): {[t for t,s in valid]}")
print(f"❌ Invalid ({len(invalid)}): {invalid}")
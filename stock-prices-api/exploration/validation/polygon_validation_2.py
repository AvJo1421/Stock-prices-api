import os
import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("POLYGON_API_KEY")

# Additional tickers to test
candidates = {
    # Telecom
    "T":    "Telecom",   # AT&T
    "VZ":   "Telecom",   # Verizon
    "TMUS": "Telecom",   # T-Mobile
    "ERIC": "Telecom",   # Ericsson
    "NOK":  "Telecom",   # Nokia

    # Insurance
    "ALL":  "Insurance", # Allstate
    "TRV":  "Insurance", # Travelers
    "CB":   "Insurance", # Chubb
    "AIG":  "Insurance", # AIG
    "AFL":  "Insurance", # Aflac
    "HIG":  "Insurance", # Hartford Financial

    # Mining
    "VALE": "Mining",    # Vale
    "FCX":  "Mining",    # Freeport McMoRan
    "NEM":  "Mining",    # Newmont
    "AA":   "Mining",    # Alcoa
    "SCCO": "Mining",    # Southern Copper
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
import os
import requests
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("POLYGON_API_KEY")

# Dynamic 2-year date range
end_date = datetime.today().strftime("%Y-%m-%d")
start_date = (datetime.today() - timedelta(days=730)).strftime("%Y-%m-%d")

print(f"Fetching from {start_date} to {end_date}\n")

# UK financial-sector watchlist (US-listed)
tickers = ["HSBC", "BCS", "LYG", "NWG", "BP", "SHEL", "UL", "AZN"]

all_data = []

for ticker in tickers:
    url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/15/minute/{start_date}/{end_date}"
    params = {
        "adjusted": "true",
        "sort": "asc",
        "limit": 50000,
        "apiKey": API_KEY
    }

    response = requests.get(url, params=params, timeout=30)

    if response.status_code == 200:
        data = response.json()
        results = data.get("results", [])
        for bar in results:
            bar["ticker"] = ticker
            all_data.append(bar)
        print(f"✓ {ticker}: {len(results)} rows")
    else:
        print(f"✗ {ticker}: failed ({response.status_code})")

# Combine into one DataFrame
df = pd.DataFrame(all_data)

# Save raw data
df.to_parquet("data_raw.parquet")

print(f"\n✅ Done. Total rows: {len(df)}")
print(df.head())
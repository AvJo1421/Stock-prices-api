import os
import requests
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("POLYGON_API_KEY")

end_date = datetime.today().strftime("%Y-%m-%d")
start_date = (datetime.today() - timedelta(days=730)).strftime("%Y-%m-%d")

print(f"Fetching from {start_date} to {end_date}\n")

# Confirmed valid tickers with sectors
WATCHLIST = {
    "HSBC": "Banking",
    "BCS":  "Banking",
    "LYG":  "Banking",
    "NWG":  "Banking",
    "DB":   "Banking",
    "SAN":  "Banking",
    "PRU":  "Insurance",
    "MET":  "Insurance",
    "BP":   "Energy",
    "SHEL": "Energy",
    "TTE":  "Energy",
    "E":    "Energy",
    "AZN":  "Pharma",
    "GSK":  "Pharma",
    "NVO":  "Pharma",
    "SNY":  "Pharma",
    "UL":   "Consumer",
    "DEO":  "Consumer",
    "BTI":  "Consumer",
    "AAPL": "Tech",
    "MSFT": "Tech",
    "NVDA": "Tech",
    "ARM":  "Tech",
    "VOD":  "Telecom",
    "RIO":  "Mining",
    "BHP":  "Mining",
}

all_data = []

for ticker, sector in WATCHLIST.items():
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
            bar["sector"] = sector
            all_data.append(bar)
        print(f"✅ {ticker} ({sector}): {len(results)} rows")
    else:
        print(f"❌ {ticker}: failed ({response.status_code})")

df = pd.DataFrame(all_data)
df.to_parquet("data_raw.parquet")
df.to_csv("data_raw.csv", index=False)

print(f"\n✅ Done. Total rows: {len(df)}")
print(f"Sectors: {df['sector'].unique()}")
print(df.head())
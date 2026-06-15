import os
import sys
import requests
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()
API_KEY = os.getenv("POLYGON_API_KEY")

start_date = "2026-01-01"
end_date = datetime.now().strftime("%Y-%m-%d")
print(f"Fetching from {start_date} to {end_date}\n")

WATCHLIST = {
    # Banking (6)
    "HSBC": "Banking", "BCS":  "Banking", "LYG":  "Banking",
    "NWG":  "Banking", "DB":   "Banking", "SAN":  "Banking",

    # Insurance (6)
    "PRU":  "Insurance", "MET": "Insurance", "ALL": "Insurance",
    "TRV":  "Insurance", "CB":  "Insurance", "AIG": "Insurance",

    # Energy (6)
    "BP":   "Energy", "SHEL": "Energy", "TTE": "Energy",
    "E":    "Energy", "XOM":  "Energy", "CVX": "Energy",

    # Pharma (6)
    "AZN":  "Pharma", "GSK": "Pharma", "NVO": "Pharma",
    "SNY":  "Pharma", "JNJ": "Pharma", "PFE": "Pharma",

    # Consumer (6)
    "UL":   "Consumer", "DEO": "Consumer", "BTI": "Consumer",
    "PG":   "Consumer", "KO":  "Consumer", "PEP": "Consumer",

    # Tech (6)
    "AAPL": "Tech", "MSFT":  "Tech", "NVDA":  "Tech",
    "ARM":  "Tech", "GOOGL": "Tech", "META":  "Tech",

    # Telecom (6)
    "VOD":  "Telecom", "T":    "Telecom", "VZ":   "Telecom",
    "TMUS": "Telecom", "ERIC": "Telecom", "NOK":  "Telecom",

    # Mining (6)
    "RIO":  "Mining", "BHP":  "Mining", "VALE": "Mining",
    "FCX":  "Mining", "NEM":  "Mining", "AA":   "Mining",
}

all_data = []

for ticker, sector in WATCHLIST.items():
    url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/15/minute/{start_date}/{end_date}"
    params = {
        "adjusted": "true",
        "sort":     "asc",
        "limit":    50000,
        "apiKey":   API_KEY
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
print(f"Tickers: {len(df['ticker'].unique())} tickers")
print(df.head())
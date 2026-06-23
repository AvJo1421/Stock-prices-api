import os
import sys
import requests
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()
API_KEY = os.getenv("POLYGON_API_KEY")

end_date = datetime.now().strftime("%Y-%m-%d")
start_date = (datetime.now() - timedelta(days=180)).strftime("%Y-%m-%d")

print(f"Fetching from {start_date} to {end_date}\n")

WATCHLIST = {
    "HSBC": "Banking", "BCS": "Banking", "LYG": "Banking",
    "NWG": "Banking", "DB": "Banking", "SAN": "Banking",
    "PRU": "Insurance", "MET": "Insurance", "ALL": "Insurance",
    "TRV": "Insurance", "CB": "Insurance", "AIG": "Insurance",
    "BP": "Energy", "SHEL": "Energy", "TTE": "Energy",
    "E": "Energy", "XOM": "Energy", "CVX": "Energy",
    "AZN": "Pharma", "GSK": "Pharma", "NVO": "Pharma",
    "SNY": "Pharma", "JNJ": "Pharma", "PFE": "Pharma",
    "UL": "Consumer", "DEO": "Consumer", "BTI": "Consumer",
    "PG": "Consumer", "KO": "Consumer", "PEP": "Consumer",
    "AAPL": "Tech", "MSFT": "Tech", "NVDA": "Tech",
    "ARM": "Tech", "GOOGL": "Tech", "META": "Tech",
    "VOD": "Telecom", "T": "Telecom", "VZ": "Telecom",
    "TMUS": "Telecom", "ERIC": "Telecom", "NOK": "Telecom",
    "RIO": "Mining", "BHP": "Mining", "VALE": "Mining",
    "FCX": "Mining", "NEM": "Mining", "AA": "Mining",
}


def fetch_ticker_data(ticker, sector, start_date, end_date, api_key, max_retries=3):
    all_results = []
    url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/15/minute/{start_date}/{end_date}"
    params = {"adjusted": "true", "sort": "asc", "limit": 50000, "apiKey": api_key}

    page = 1
    while url:
        for attempt in range(max_retries):
            try:
                response = requests.get(url, params=params, timeout=30)
                if response.status_code == 200:
                    break
                elif attempt == max_retries - 1:
                    print(f"❌ {ticker}: failed after {max_retries} attempts ({response.status_code})")
                    return ticker, sector, all_results
            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    print(f"❌ {ticker}: connection error - {e}")
                    return ticker, sector, all_results

        data = response.json()
        results = data.get("results", [])
        for bar in results:
            bar["ticker"] = ticker
            bar["sector"] = sector
            all_results.append(bar)

        next_url = data.get("next_url")
        if next_url:
            url = next_url
            params = {"apiKey": api_key}
            page += 1
        else:
            url = None

    print(f"✅ {ticker} ({sector}): {len(all_results)} rows ({page} page{'s' if page > 1 else ''})")
    return ticker, sector, all_results


all_data = []
failed_tickers = []

with ThreadPoolExecutor(max_workers=10) as executor:
    futures = {
        executor.submit(fetch_ticker_data, ticker, sector, start_date, end_date, API_KEY): ticker
        for ticker, sector in WATCHLIST.items()
    }

    for future in as_completed(futures):
        ticker, sector, results = future.result()
        if not results:
            failed_tickers.append(ticker)
        all_data.extend(results)

# --- Validation ---
fetched_tickers = set(WATCHLIST.keys()) - set(failed_tickers)
print(f"\n📊 Fetched {len(fetched_tickers)}/{len(WATCHLIST)} tickers successfully")

if failed_tickers:
    print(f"⚠️  Failed tickers: {failed_tickers}")

if len(all_data) == 0:
    print("❌ CRITICAL: No data fetched at all. Aborting.")
    sys.exit(1)

if len(fetched_tickers) < len(WATCHLIST) * 0.8:
    print(f"❌ CRITICAL: Less than 80% of tickers fetched successfully. Aborting to avoid corrupting good data.")
    sys.exit(1)

df = pd.DataFrame(all_data)
df.to_parquet("data_raw.parquet")
df.to_csv("data_raw.csv", index=False)

print(f"\n✅ Done. Total rows: {len(df)}")
print(f"Sectors: {df['sector'].unique()}")
print(f"Tickers: {len(df['ticker'].unique())} tickers")
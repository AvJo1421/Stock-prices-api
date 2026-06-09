from dotenv import load_dotenv
import os
import requests

load_dotenv()

API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")

symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA"]

for symbol in symbols:
    url = (
        f"https://www.alphavantage.co/query"
        f"?function=GLOBAL_QUOTE"
        f"&symbol={symbol}"
        f"&apikey={API_KEY}"
    )

    response = requests.get(url)
    data = response.json()

    print(f"\n{symbol}")
    print(data)
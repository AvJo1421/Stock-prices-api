import os
import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("POLYGON_API_KEY")

# Try a UK ticker — testing different formats
ticker = "VOD"   # Vodafone — we'll see if it resolves

url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/day/2025-11-03/2025-11-28"
params = {"adjusted": "true", "sort": "asc", "limit": 120, "apiKey": API_KEY}

response = requests.get(url, params=params, timeout=30)
print("Status:", response.status_code)
print("Raw response:", response.text[:500])
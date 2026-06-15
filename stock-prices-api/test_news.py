import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("POLYGON_API_KEY")

response = requests.get(
    "https://api.polygon.io/v2/reference/news",
    params={
        "ticker": "NVDA",
        "limit": 3,
        "apiKey": API_KEY
    }
)

print(response.status_code)
print(json.dumps(response.json(), indent=2))
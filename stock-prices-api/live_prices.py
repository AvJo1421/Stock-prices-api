import asyncio
import json
import os
from dotenv import load_dotenv
import websockets

load_dotenv()

API_KEY = os.getenv("POLYGON_API_KEY")

TICKERS = [
    "HSBC", "BCS", "LYG", "NWG", "DB", "SAN",
    "PRU", "MET", "ALL", "TRV", "CB", "AIG",
    "BP", "SHEL", "TTE", "E", "XOM", "CVX",
    "AZN", "GSK", "NVO", "SNY", "JNJ", "PFE",
    "UL", "DEO", "BTI", "PG", "KO", "PEP",
    "AAPL", "MSFT", "NVDA", "ARM", "GOOGL", "META",
    "VOD", "T", "VZ", "TMUS", "ERIC", "NOK",
    "RIO", "BHP", "VALE", "FCX", "NEM", "AA"
]

async def connect():
    url = "wss://delayed.polygon.io/stocks"

    async with websockets.connect(url) as ws:
        # Authenticate
        await ws.send(json.dumps({"action": "auth", "params": API_KEY}))
        print(await ws.recv())

        # Subscribe to all tickers
        tickers_str = ",".join([f"A.{t}" for t in TICKERS])
        await ws.send(json.dumps({"action": "subscribe", "params": tickers_str}))
        print(await ws.recv())

        # Listen
        while True:
            msg = await ws.recv()
            data = json.loads(msg)
            for item in data:
                if item.get("ev") == "A":
                    print(f"{item['sym']} | Close: {item['c']} | Volume: {item['v']}")

asyncio.run(connect())
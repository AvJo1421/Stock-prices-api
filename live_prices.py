import os
import json
import websocket
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("POLYGON_API_KEY")

TICKERS = ["HSBC", "BCS", "BP", "SHEL"]
SUBSCRIBE_CHANNELS = [f"A.{t}" for t in TICKERS]

def on_open(ws):
    print("✓ Connected to Polygon WebSocket")

def on_message(ws, message):
    data = json.loads(message)
    for event in data:
        ev = event.get("ev")
        status = event.get("status")
        msg = event.get("message", "")

        if ev == "status" and status == "connected":
            print("✓ Welcome received — authenticating...")
            ws.send(json.dumps({"action": "auth", "params": API_KEY}))

        elif ev == "status" and status == "auth_success":
            print("✓ Authenticated — subscribing...")
            ws.send(json.dumps({
                "action": "subscribe",
                "params": ",".join(SUBSCRIBE_CHANNELS)
            }))

        elif ev == "status" and status == "error":
            print(f"✗ Error: {msg}")

        elif ev == "A":
            ticker = event.get("sym")
            close  = event.get("c")
            volume = event.get("av")
            print(f"  📈 {ticker}  close: ${close}  volume: {volume:,}")

def on_error(ws, error):
    print(f"✗ Error: {error}")

def on_close(ws, close_status_code, close_msg):
    print("Connection closed")

ws = websocket.WebSocketApp(
    "wss://delayed.polygon.io/stocks",   # ← only change
    on_open=on_open,
    on_message=on_message,
    on_error=on_error,
    on_close=on_close,
)

print("Connecting...")
ws.run_forever()
import asyncio
import websockets
import json

async def test_websocket():
    """Connect to WebSocket and listen for predictions"""
    uri = "ws://localhost:8000/ws/predictions"

    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to WebSocket")
            print("Listening for predictions...\n")

            while True:
                message = await websocket.recv()
                data = json.loads(message)

                ticker = data.get("ticker")
                current = data.get("current_price")
                predicted = data.get("predicted_price")
                change = data.get("change_pct")

                print(f"📊 {ticker}")
                print(f"   Current:   ${current:.2f}")
                print(f"   Predicted: ${predicted:.2f}")
                print(f"   Change:    {change:+.2f}%")
                print()

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket())

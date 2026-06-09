import asyncio
import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv
import pandas as pd
import numpy as np
import requests
import joblib
from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.responses import JSONResponse
import logging

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")
logger = logging.getLogger(__name__)

app = FastAPI(title="Stock Price Prediction API")

# Global state
model = None
feature_cols = None
connected_clients = set()
latest_predictions = {}


@app.on_event("startup")
async def startup():
    global model, feature_cols
    try:
        model = joblib.load("stock_price_model.pkl")
        feature_cols = [
            "return", "log_return", "rolling_vol_20", "rolling_vol_50",
            "volume_zscore", "sma_20", "sma_50", "momentum", "intraday_range",
            "price_zscore", "volume", "vwap", "open", "high", "low", "transactions"
        ]
        print("✅ Model loaded")

        tickers = ["AAPL", "MSFT", "NVDA", "HSBC", "BP"]
        asyncio.create_task(poll_polygon(tickers))
    except Exception as e:
        print(f"❌ Failed to load model: {e}")
        raise


def fetch_polygon_data(ticker: str):
    """Fetch latest 15-min aggregated data from Polygon"""
    url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/minute"
    params = {
        "timespan": "minute",
        "adjusted": "true",
        "sort": "desc",
        "limit": 100,
        "apiKey": POLYGON_API_KEY
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json().get("results", [])
            return pd.DataFrame(data) if data else None
    except Exception as e:
        logger.error(f"Polygon fetch error for {ticker}: {e}")
    return None


def engineer_features(df: pd.DataFrame) -> dict:
    """Engineer features from raw OHLCV data"""
    if df is None or len(df) < 50:
        return None

    df = df.sort_values("t").reset_index(drop=True)

    # Convert timestamp
    df["timestamp"] = pd.to_datetime(df["t"], unit="ms")
    df["close"] = df["c"]
    df["volume"] = df["v"]
    df["vwap_val"] = df["vw"]
    df["open"] = df["o"]
    df["high"] = df["h"]
    df["low"] = df["l"]

    # Calculate features
    df["return"] = df["close"].pct_change()
    df["log_return"] = np.log(df["close"] / df["close"].shift(1))
    df["rolling_vol_20"] = df["return"].rolling(20).std()
    df["rolling_vol_50"] = df["return"].rolling(50).std()

    df["volume_zscore"] = (
        (df["volume"] - df["volume"].rolling(20).mean())
        / df["volume"].rolling(20).std()
    )

    df["sma_20"] = df["close"].rolling(20).mean()
    df["sma_50"] = df["close"].rolling(50).mean()
    df["momentum"] = df["sma_20"] - df["sma_50"]
    df["intraday_range"] = (df["high"] - df["low"]) / df["close"]

    df["price_zscore"] = (
        (df["close"] - df["close"].rolling(20).mean())
        / df["close"].rolling(20).std()
    )
    df["transactions"] = df["n"]

    # Get latest row
    latest = df.iloc[-1].to_dict()
    return latest


async def broadcast_prediction(ticker: str, prediction: float, price: float, timestamp: str):
    """Broadcast prediction to all connected WebSocket clients"""
    message = {
        "ticker": ticker,
        "predicted_price": float(prediction),
        "current_price": float(price),
        "timestamp": timestamp,
        "change_pct": round(((prediction - price) / price) * 100, 2)
    }

    # Store latest
    latest_predictions[ticker] = message

    # Broadcast to all clients
    disconnected = set()
    for client in connected_clients:
        try:
            await client.send_json(message)
        except:
            disconnected.add(client)

    # Cleanup disconnected
    connected_clients.difference_update(disconnected)


async def poll_polygon(tickers: list, interval_seconds: int = 900):
    """Background task: poll Polygon every 15 mins and send predictions"""
    while True:
        try:
            for ticker in tickers:
                df = fetch_polygon_data(ticker)
                features = engineer_features(df)

                if features and model:
                    # Prepare feature vector
                    X = np.array([[
                        features.get("return", 0),
                        features.get("log_return", 0),
                        features.get("rolling_vol_20", 0),
                        features.get("rolling_vol_50", 0),
                        features.get("volume_zscore", 0),
                        features.get("sma_20", features.get("close", 0)),
                        features.get("sma_50", features.get("close", 0)),
                        features.get("momentum", 0),
                        features.get("intraday_range", 0),
                        features.get("price_zscore", 0),
                        features.get("volume", 0),
                        features.get("vwap_val", 0),
                        features.get("open", 0),
                        features.get("high", 0),
                        features.get("low", 0),
                        features.get("transactions", 0),
                    ]])

                    prediction = model.predict(X)[0]
                    current_price = features.get("close", 0)
                    timestamp = datetime.utcnow().isoformat()

                    await broadcast_prediction(ticker, prediction, current_price, timestamp)
                    print(f"📊 {ticker}: ${current_price:.2f} → ${prediction:.2f}")

        except Exception as e:
            logger.error(f"Poll error: {e}")

        await asyncio.sleep(interval_seconds)


@app.get("/")
async def root():
    return {"message": "Stock Price Prediction API", "status": "running"}


@app.get("/latest/{ticker}")
async def get_latest(ticker: str):
    """Get latest prediction for a ticker"""
    if ticker not in latest_predictions:
        raise HTTPException(status_code=404, detail=f"No predictions for {ticker}")
    return latest_predictions[ticker]


@app.get("/latest")
async def get_all_latest():
    """Get all latest predictions"""
    return latest_predictions


@app.post("/predict/{ticker}")
async def predict_single(ticker: str):
    """On-demand prediction for a ticker"""
    df = fetch_polygon_data(ticker)
    features = engineer_features(df)

    if not features:
        raise HTTPException(status_code=400, detail="Insufficient data")

    X = np.array([[
        features.get("return", 0),
        features.get("log_return", 0),
        features.get("rolling_vol_20", 0),
        features.get("rolling_vol_50", 0),
        features.get("volume_zscore", 0),
        features.get("sma_20", features.get("close", 0)),
        features.get("sma_50", features.get("close", 0)),
        features.get("momentum", 0),
        features.get("intraday_range", 0),
        features.get("price_zscore", 0),
        features.get("volume", 0),
        features.get("vwap_val", 0),
        features.get("open", 0),
        features.get("high", 0),
        features.get("low", 0),
        features.get("transactions", 0),
    ]])

    prediction = model.predict(X)[0]
    return {
        "ticker": ticker,
        "predicted_price": float(prediction),
        "current_price": float(features.get("close", 0)),
        "timestamp": datetime.utcnow().isoformat()
    }


@app.websocket("/ws/predictions")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for live prediction streaming"""
    await websocket.accept()
    connected_clients.add(websocket)

    # Send all latest predictions on connect
    for prediction in latest_predictions.values():
        await websocket.send_json(prediction)

    try:
        while True:
            # Keep connection alive, wait for any client messages
            data = await websocket.receive_text()
    except:
        connected_clients.discard(websocket)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

import pandas as pd
import numpy as np

# Load clean data
df = pd.read_parquet("data_clean.parquet")
print(f"Loaded: {df.shape}")

featured = []

for ticker in df["ticker"].unique():
    data = df[df["ticker"] == ticker].copy()
    data = data.sort_values("timestamp").reset_index(drop=True)

    # 1. Returns
    data["return"]     = data["close"].pct_change()
    data["log_return"] = np.log(data["close"] / data["close"].shift(1))

    # 2. Rolling volatility
    data["rolling_vol_20"] = data["return"].rolling(20).std()
    data["rolling_vol_50"] = data["return"].rolling(50).std()

    # 3. Volume z-score
    data["volume_zscore"] = (
        (data["volume"] - data["volume"].rolling(20).mean())
        / data["volume"].rolling(20).std()
    )

    # 4. Price momentum
    data["sma_20"]   = data["close"].rolling(20).mean()
    data["sma_50"]   = data["close"].rolling(50).mean()
    data["momentum"] = data["sma_20"] - data["sma_50"]

    # 5. Intraday range
    data["intraday_range"] = (data["high"] - data["low"]) / data["close"]

    # 6. Price relative to rolling mean — how far from normal?
    data["price_zscore"] = (
        (data["close"] - data["close"].rolling(20).mean())
        / data["close"].rolling(20).std()
    )

    featured.append(data)

# Combine
df_featured = pd.concat(featured).reset_index(drop=True)

# Drop NaN rows from rolling windows
df_featured = df_featured.dropna().reset_index(drop=True)

# Save
df_featured.to_parquet("data_featured.parquet")
df_featured.to_csv("data_featured.csv", index=False)

print(f"Featured shape: {df_featured.shape}")
print(f"\nColumns: {df_featured.columns.tolist()}")
print(df_featured.head())
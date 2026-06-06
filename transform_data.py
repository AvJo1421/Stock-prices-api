import pandas as pd

# Load raw data (bronze layer)
df = pd.read_parquet("data_raw.parquet")

print("Before transformation:")
print(df.head())
print(f"Shape: {df.shape}\n")

# Step 1 — Rename columns to readable names
df = df.rename(columns={
    "v":  "volume",
    "vw": "vwap",
    "o":  "open",
    "c":  "close",
    "h":  "high",
    "l":  "low",
    "t":  "timestamp",
    "n":  "transactions"
})

# Step 2 — Fix timestamp (Unix milliseconds → readable datetime)
df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)

# Optional but nice — convert UTC to London time
df["timestamp"] = df["timestamp"].dt.tz_convert("Europe/London")

# Sort by ticker and timestamp
df = df.sort_values(["ticker", "timestamp"]).reset_index(drop=True)

# Save clean data (silver layer)
df.to_parquet("data_clean.parquet")

print("After transformation:")
print(df.head())
print(f"\nShape: {df.shape}")
print(f"\nDate range: {df['timestamp'].min()} → {df['timestamp'].max()}")
print(f"\nTickers: {df['ticker'].unique()}")

# Save as CSV too
df.to_csv("data_clean.csv", index=False)
print("\n✅ CSV saved: data_clean.csv")
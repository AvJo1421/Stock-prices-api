import pandas as pd
import chromadb

# --- Load parquet ---
df = pd.read_parquet("data_clean.parquet")

# --- Setup ChromaDB ---
client = chromadb.PersistentClient(path="./chroma_db")

# Delete old collection if exists
try:
    client.delete_collection(name="stock_data")
    print("Old collection deleted")
except:
    pass

collection = client.create_collection(name="stock_data")

# --- Load data into ChromaDB ---
documents = []
metadatas = []
ids = []

for i, row in df.iterrows():
    doc = (
        f"{row['ticker']} on {row['timestamp']} — "
        f"open: {row['open']}, high: {row['high']}, "
        f"low: {row['low']}, close: {row['close']}, "
        f"volume: {row['volume']}"
    )
    documents.append(doc)
    metadatas.append({"ticker": row["ticker"], "timestamp": str(row["timestamp"])})
    ids.append(str(i))

# --- Add in batches ---
batch_size = 5000
for i in range(0, len(documents), batch_size):
    collection.add(
        documents=documents[i:i+batch_size],
        metadatas=metadatas[i:i+batch_size],
        ids=ids[i:i+batch_size]
    )
    print(f"Loaded {min(i+batch_size, len(documents))} / {len(documents)} rows")

print("Done!")
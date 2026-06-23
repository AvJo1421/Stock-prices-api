import chromadb

client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection(name="stock_data")

results = collection.query(
    query_texts=["META highest close November 2025"],
    n_results=5,
    where={"ticker": "META"}
)

for doc in results["documents"][0]:
    print(doc)
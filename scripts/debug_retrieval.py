import chromadb
from chromadb.utils import embedding_functions
import os

persist_dir = "./chroma_db"
client = chromadb.PersistentClient(path=persist_dir)
embedding_fn = embedding_functions.DefaultEmbeddingFunction()

collection = client.get_collection(name="client_interactions", embedding_function=embedding_fn)

print(f"Total interaction records in ChromaDB: {collection.count()}")

# Check for specific IDs
ids_to_check = ["INT-6113", "INT-6114", "INT-6115"]
results = collection.get(ids=ids_to_check)
print(f"Found IDs {ids_to_check}: {results['ids']}")

# Search for the query
query = "What was discussed regarding Generative AI Governance with GlobalFin Bank?"
search_results = collection.query(query_texts=[query], n_results=5)
print(f"\nSearch results for '{query}':")
for i, rid in enumerate(search_results['ids'][0]):
    print(f"Rank {i+1}: ID={rid}")

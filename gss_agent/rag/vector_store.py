import chromadb
from chromadb.utils import embedding_functions
import json
import os

class NexusVectorStore:
    def __init__(self, persist_directory="./chroma_db"):
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.embedding_fn = embedding_functions.DefaultEmbeddingFunction()
        
        # Collections
        self.research_collection = self.client.get_or_create_collection(
            name="nexus_research",
            embedding_function=self.embedding_fn
        )
        self.interaction_collection = self.client.get_or_create_collection(
            name="client_interactions",
            embedding_function=self.embedding_fn
        )

    def ingest_research(self, content_file):
        with open(content_file, "r") as f:
            content = json.load(f)
        
        documents = [f"{item['title']}\n\n{item['abstract']}\n\nStrategic Value: {item['strategic_value']}" for item in content]
        metadatas = [{"id": item["id"], "title": item["title"], "tags": ",".join(item["tags"])} for item in content]
        ids = [item["id"] for item in content]
        
        self.research_collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        print(f"Ingested {len(ids)} research papers into ChromaDB.")

    def ingest_interactions(self, interaction_file):
        with open(interaction_file, "r") as f:
            interactions = json.load(f)
        
        documents = [f"Client: {item['client_name']}\nType: {item['type']}\nSummary: {item['summary']}\nActions: {', '.join(item['actions_identified'])}" for item in interactions]
        metadatas = [{"id": item["id"], "client_id": item["client_id"], "client_name": item["client_name"], "sentiment": item["sentiment"]} for item in interactions]
        ids = [item["id"] for item in interactions]
        
        self.interaction_collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        print(f"Ingested {len(ids)} interaction records into ChromaDB.")

    def search_research(self, query, n_results=5):
        results = self.research_collection.query(
            query_texts=[query],
            n_results=n_results
        )
        return results

    def search_interactions(self, query, client_id=None, n_results=5):
        where = {"client_id": client_id} if client_id else None
        results = self.interaction_collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where
        )
        return results

if __name__ == "__main__":
    v_store = NexusVectorStore()
    
    # Absolute paths for data files
    base_dir = "/Users/govindmittal/datascience-setup/interview_prep/gartner/gss_agent/data"
    
    v_store.ingest_research(os.path.join(base_dir, "content.json"))
    v_store.ingest_interactions(os.path.join(base_dir, "interactions.json"))
    
    # Test query
    test_results = v_store.search_research("Agentic AI trends 2025")
    print(f"Test Query Result Count: {len(test_results['ids'][0])}")

import os
import sys
from gss_agent.rag.vector_store import NexusVectorStore

def main():
    print("🚀 Starting Data Ingestion into Nexus Advisory Vector Store...")
    
    # Initialize vector store
    v_store = NexusVectorStore(persist_directory="./chroma_db")
    
    # Relative paths for data files
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), "gss_agent", "data")
    
    # Ingest Research Content (Phase 1.3)
    content_path = os.path.join(DATA_DIR, "content.json")
    if os.path.exists(content_path):
        print(f"Ingesting research from {content_path}...")
        v_store.ingest_research(content_path)
    else:
        print(f"⚠️ Research file not found: {content_path}")

    # Ingest Interactions (Phase 1.4)
    # Note: This will ingest what's currently generated. We can re-run later for full dataset.
    interactions_path = os.path.join(DATA_DIR, "interactions.json")
    if os.path.exists(interactions_path):
        print(f"Ingesting interactions from {interactions_path}...")
        v_store.ingest_interactions(interactions_path)
    else:
        print(f"⚠️ Interactions file not found: {interactions_path}")

    # Note: Other data (clients, metrics, associates, contracts) are typically stored in relational/JSON
    # but some metadata could be indexed if needed. For now, the core RAG targets research and interactions.
    
    print("\n✅ Ingestion Complete. Vector store is ready for queries.")

if __name__ == "__main__":
    main()

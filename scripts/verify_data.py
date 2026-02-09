import json
import os
import chromadb
from pprint import pprint

def verify_json_content():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # 1. Verify Interactions
    int_path = os.path.join(base_dir, "gss_agent/data/generated_interactions_llm.json")
    print(f"\n--- Verifying Transcripts ({int_path}) ---")
    if os.path.exists(int_path):
        with open(int_path, "r") as f:
            data = json.load(f)
        print(f"✅ Found {len(data)} transcripts.")
        if data:
            print("Sample Transcript Snippet:")
            print(data[0]['content'][:200] + "...")
            print(f"Model used signals: {data[0].get('actions_identified', 'N/A')}")
    else:
        print("❌ Interactions file NOT FOUND.")

    # 2. Verify Research
    res_path = os.path.join(base_dir, "gss_agent/data/content.json")
    print(f"\n--- Verifying Research ({res_path}) ---")
    if os.path.exists(res_path):
        with open(res_path, "r") as f:
            data = json.load(f)
        # Check first 5 for valid abstracts (not Lorem Ipsum)
        valid_count = sum(1 for d in data[:10] if "Civil wide" not in d['abstract'] and len(d['abstract']) > 20)
        print(f"✅ Research Items Checked: {len(data)}")
        print(f"✅ Valid Abstracts (Sampled first 10): {valid_count}/10")
        if data:
            print("Sample Abstract:")
            print(data[0]['abstract'])
    else:
        print("❌ Research file NOT FOUND.")

def verify_vector_store():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(base_dir, "chroma_db")
    
    print(f"\n--- Verifying ChromaDB ({db_path}) ---")
    try:
        client = chromadb.PersistentClient(path=db_path)
        
        # Interactions
        col_int = client.get_collection("client_interactions")
        count_int = col_int.count()
        print(f"✅ Client Interactions Collection Count: {count_int}")
        
        # Research
        col_res = client.get_collection("gartner_research")
        count_res = col_res.count()
        print(f"✅ Gartner Research Collection Count: {count_res}")
        
        # Test Query
        results = col_int.query(query_texts=["renewal budget cuts"], n_results=1)
        if results['documents'][0]:
            print(f"✅ Test Query 'renewal budget cuts' found match: {results['metadatas'][0][0]['client_name']}")
        else:
            print("❌ Test Query FAILED.")
            
    except Exception as e:
        print(f"❌ ChromaDB Verification Failed: {e}")

if __name__ == "__main__":
    verify_json_content()
    verify_vector_store()

import json
import os
import sys

# Add root to sys.path
sys.path.append(os.getcwd())

from gss_agent.core.tools import search_interaction_history, lookup_client_file, analyze_data_python
from gss_agent.rag.vector_store import NexusVectorStore

def test_filtering():
    print("--- [TEST: SEARCH FILTERING] ---")
    # Test with a specific client
    res1 = search_interaction_history.invoke({"query": "AI strategy", "client_name": "Metro Manufacturing"})
    print(f"Metro Mfg Result Found: {bool(res1 and 'No relevant' not in res1)}")
    
    # Test with a non-existent client
    res2 = search_interaction_history.invoke({"query": "AI strategy", "client_name": "NonExistentClient"})
    print(f"NonExistentClient Error: {res2}")
    
    # Test without client (global)
    res3 = search_interaction_history.invoke({"query": "AI strategy"})
    print(f"Global Search Found: {bool(res3 and 'No relevant' not in res3)}")

def test_data_integrity():
    print("\n--- [TEST: DATA INTEGRITY] ---")
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATA_DIR = os.path.join(os.getcwd(), "gss_agent", "data")
    
    with open(os.path.join(DATA_DIR, "interactions.json"), "r") as f:
        interactions = json.load(f)
    
    # Check for garbled text
    garbled_keywords = ["\u2014", "\u201d", "\u201c", "\u2019", "\u00a0"]
    found_garbled = False
    for item in interactions:
        content = item.get("content", "")
        for k in garbled_keywords:
            if k in content:
                print(f"Found garbled char '{k}' in {item['id']}")
                found_garbled = True
                break
    
    print(f"Garbled text check passed: {not found_garbled}")
    print(f"Total records: {len(interactions)}")

def test_sandbox_safety():
    print("\n--- [TEST: SANDBOX SAFETY] ---")
    # Test blocked patterns
    res1 = analyze_data_python.invoke("import os; os.listdir('.')")
    print(f"Blocked 'os.': {'Success' if 'blocked' in res1.lower() else 'Fail'}")
    
    res2 = analyze_data_python.invoke("import multiprocessing; print('hi')")
    print(f"Blocked 'multiprocessing': {'Success' if 'blocked' in res2.lower() else 'Fail'}")

if __name__ == "__main__":
    test_filtering()
    test_data_integrity()
    test_sandbox_safety()

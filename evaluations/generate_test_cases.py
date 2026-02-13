import json
import os
import random

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "gss_agent", "data")
TEST_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_data")

def generate_retrieval_cases():
    with open(os.path.join(DATA_DIR, "content.json")) as f:
        content = json.load(f)
    with open(os.path.join(DATA_DIR, "interactions.json")) as f:
        interactions = json.load(f)
        
    cases = []
    
    # 1. Use Research Titles as queries
    for c in content[:10]:
        cases.append({
            "query": f"Find information about {c['title']}",
            "expected_doc_ids": [c["id"]],
            "category": "research"
        })
        
    # 2. Use Interaction key topics
    for i in interactions[-10:]: # Use some of the newly generated ones
        if i.get("key_topics"):
            topic = i["key_topics"][0]
            cases.append({
                "query": f"What was discussed regarding {topic} with {i['client_name']}?",
                "expected_doc_ids": [i["id"]],
                "category": "interaction"
            })
            
    with open(os.path.join(TEST_DATA_DIR, "retrieval_cases.json"), "w") as f:
        json.dump(cases, f, indent=2)
    print(f"Generated {len(cases)} retrieval cases.")

def generate_tool_usage_cases():
    # Simple predefined logic for trajectory matching
    cases = [
        {
            "query": "Give me a full health check for Nexus Innovations",
            "expected_tools": ["lookup_client_file", "get_client_engagement_metrics", "search_interaction_history"]
        },
        {
            "query": "Find recent research on Agentic AI for Pinnacle Capital",
            "expected_tools": ["search_research_library"]
        },
        {
            "query": "What is the total revenue risk for my portfolio?",
            "expected_tools": ["get_at_risk_clients_summary", "get_revenue_snapshot"]
        }
    ]
    with open(os.path.join(TEST_DATA_DIR, "tool_usage_cases.json"), "w") as f:
        json.dump(cases, f, indent=2)
    print(f"Generated {len(cases)} tool usage cases.")

if __name__ == "__main__":
    os.makedirs(TEST_DATA_DIR, exist_ok=True)
    generate_retrieval_cases()
    generate_tool_usage_cases()

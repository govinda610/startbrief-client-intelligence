import json
import os
import random
import time
from datetime import datetime, timedelta
from typing import List, Optional
from pydantic import BaseModel, Field
from gss_agent.data.llm_config import llm_rotator

# Configuration
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "gss_agent", "data")
CLIENTS_FILE = os.path.join(DATA_DIR, "clients.json")
OUTPUT_FILE = os.path.join(DATA_DIR, "interactions.json")

# Constants
BATCH_SIZE = 4
REQUEST_LIMIT = 80
TARGET_NEW_INTERACTIONS = 200
SENTIMENT_LABEL_TARGET = 60 # Aim for slightly more than 50

INTERACTION_TYPES = [
    "Phone Call Transcript",
    "Email Thread",
    "Meeting Note",
    "Support Ticket",
    "Analyst Inquiry Call"
]

class InteractionItem(BaseModel):
    type: str
    content: str
    sentiment: str
    key_topics: List[str]
    actions_identified: List[str]

class InteractionBatch(BaseModel):
    interactions: List[InteractionItem]

def generate_interaction_batch_zai(client, items_to_generate, add_true_sentiment=False):
    """Generate a batch of interactions using ZAI to respect request limits"""
    
    word_counts = {
        "Phone Call Transcript": "1000-1500 words",
        "Email Thread": "600-900 words",
        "Meeting Note": "500-800 words",
        "Support Ticket": "300-500 words",
        "Analyst Inquiry Call": "800-1200 words"
    }
    
    types_str = ", ".join(items_to_generate)
    
    prompt = f"""
    Generate {len(items_to_generate)} realistic and detailed Nexus Advisory client interactions as a JSON array.
    
    Client: {client['name']} ({client['industry']})
    Interaction Types to Generate: {types_str}
    
    Requirements per type:
    - Phone Call Transcript: 1000-1500 words (Marcus: ... Sofia: ...)
    - Email Thread: 600-900 words (include headers/multi-turn)
    - Meeting Note: 500-800 words
    - Support Ticket: 300-500 words
    - Analyst Inquiry Call: 800-1200 words
    
    Format: Return ONLY a JSON object with a single key 'interactions' which is a list of objects.
    Each object must have: "type", "content", "sentiment", "key_topics", "actions_identified".
    
    Realism: Use specific Nexus Advisory research titles (Magic Quadrants, Hype Cycles).
    Sentiment: Vary the sentiment (Positive, Negative, Neutral) across the batch.
    
    Return ONLY valid JSON. No preamble.
    """
    
    system_prompt = "You are a Senior Nexus Advisory Executive Partner. Return ONLY valid JSON."
    
    llm_rotator.use_zai_fallback = True
    
    try:
        # Using generate_structured for robust ZAI JSON capture
        batch = llm_rotator.generate_structured(prompt, InteractionBatch, system_prompt, max_tokens=8000)
        return batch.interactions
    except Exception as e:
        print(f"  ❌ ZAI Batch Generation Error: {e}")
        return None

def main():
    print(f"--- Nexus Interaction Data Fix Script ---")
    
    # 1. Load data
    with open(CLIENTS_FILE, "r") as f:
        clients = json.load(f)
    
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r") as f:
            all_interactions = json.load(f)
    else:
        all_interactions = []

    # 2. Cleanup: Remove empty Batch 1 records (INT-3xxx/INT-4xxx)
    initial_count = len(all_interactions)
    all_interactions = [i for i in all_interactions if not (i['id'].startswith("INT-3") or i['id'].startswith("INT-4"))]
    print(f"Removed {initial_count - len(all_interactions)} empty placeholder records.")

    # 3. Plan Generation
    # Current Batch 2 is INT-5xxx. New batch will be INT-6xxx.
    next_id = 6000
    # Find max existing 6xxx if we are resuming
    existing_6k = [int(i['id'].split('-')[1]) for i in all_interactions if i['id'].startswith("INT-6")]
    if existing_6k:
        next_id = max(existing_6k) + 1

    sentiment_labels_added = sum(1 for i in all_interactions if "true_sentiment" in i)
    total_new_needed = TARGET_NEW_INTERACTIONS - len([i for i in all_interactions if i['id'].startswith("INT-6")])
    
    if total_new_needed <= 0:
        print("Target for new interactions already met.")
    else:
        print(f"Target: {total_new_needed} new interactions in batches of {BATCH_SIZE}.")
        
        start_date = datetime(2025, 8, 1)
        end_date = datetime(2026, 2, 28)
        
        # Distribute across clients
        client_pool = clients * 10 # ensure enough cycles
        processed_count = 0
        
        for client in client_pool:
            if processed_count >= total_new_needed:
                break
                
            batch_items = []
            for _ in range(BATCH_SIZE):
                batch_items.append(random.choice(INTERACTION_TYPES))
            
            print(f"\nProcessing Batch for {client['name']} ({processed_count}/{total_new_needed})...")
            
            # Request limit awareness: roughly 1 request per batch.
            # 200 interactions / 4 = 50 requests. 
            # Give ZAI some breathing room.
            time.sleep(2)
            
            # Should we add true_sentiment labels to this batch?
            should_label = sentiment_labels_added < SENTIMENT_LABEL_TARGET
            
            results = generate_interaction_batch_zai(client, batch_items)
            
            if results:
                for res in results:
                    days_offset = random.randint(0, (end_date - start_date).days)
                    interaction_date = start_date + timedelta(days=days_offset)
                    
                    record = {
                        "id": f"INT-{next_id}",
                        "client_id": client["id"],
                        "client_name": client["name"],
                        "date": interaction_date.strftime("%Y-%m-%d"),
                        "type": res.type,
                        "content": res.content,
                        "summary": res.content[:300] + "...",
                        "sentiment": res.sentiment,
                        "key_topics": res.key_topics,
                        "actions_identified": res.actions_identified
                    }
                    
                    if sentiment_labels_added < SENTIMENT_LABEL_TARGET:
                        record["true_sentiment"] = res.sentiment
                        sentiment_labels_added += 1
                        
                    all_interactions.append(record)
                    next_id += 1
                    processed_count += 1
                
                # Save incrementally
                with open(OUTPUT_FILE, "w") as f:
                    json.dump(all_interactions, f, indent=2)
                print(f"  ✅ Saved batch of {len(results)}. Total: {len(all_interactions)}. Sentiment labels: {sentiment_labels_added}")
            else:
                print(f"  ❌ Batch failed. Skipping.")
                time.sleep(5) # Cooldown on failure

    # Final check: make sure we have enough sentiment labels even if batching failed or we were done
    if sentiment_labels_added < 50:
        print(f"Adding sentiment labels to existing records to reach target of 50...")
        for i in all_interactions:
            if sentiment_labels_added >= 50: break
            if "true_sentiment" not in i:
                i["true_sentiment"] = i["sentiment"]
                sentiment_labels_added += 1
        with open(OUTPUT_FILE, "w") as f:
            json.dump(all_interactions, f, indent=2)

    print(f"\n✅ Interaction Data Fix Complete.")
    print(f"Final count: {len(all_interactions)}")
    print(f"Sentiment labels: {sentiment_labels_added}")

if __name__ == "__main__":
    main()

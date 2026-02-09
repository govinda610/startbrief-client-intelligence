import json
import os
import random
import time
from datetime import datetime, timedelta
from typing import List
from pydantic import BaseModel, Field
from gss_agent.data.llm_config import llm_rotator

DATA_DIR = "/Users/govindmittal/datascience-setup/interview_prep/gartner/gss_agent/data"
CLIENTS_FILE = os.path.join(DATA_DIR, "clients.json")
OUTPUT_FILE = os.path.join(DATA_DIR, "interactions.json")

INTERACTION_TYPES = [
    "Phone Call Transcript",
    "Email Thread",
    "Meeting Note",
    "Support Ticket",
    "Analyst Inquiry Call"
]

class DetailedInteraction(BaseModel):
    type: str = Field(..., description="Interaction type")
    content: str = Field(..., description="Detailed content (1500-3000 words for calls, 800-1500 for emails)")
    sentiment: str = Field(..., description="Overall sentiment")
    key_topics: List[str] = Field(..., description="Main topics discussed")
    actions_identified: List[str] = Field(..., description="Action items")

def generate_detailed_interaction_zai(client, interaction_type):
    """Generate one detailed interaction using ZAI for maximum quality"""
    
    # Scaled back word counts for better stability as requested
    word_counts = {
        "Phone Call Transcript": "600-1000 words",
        "Email Thread": "400-800 words",
        "Meeting Note": "400-700 words",
        "Support Ticket": "300-600 words",
        "Analyst Inquiry Call": "500-900 words"
    }
    
    word_requirement = word_counts.get(interaction_type, "500-800 words")
    
    prompt = f"""
    Generate a realistic and detailed {interaction_type} for this Gartner client.
    
    Client: {client['name']} ({client['industry']})
    
    Requirements:
    1. Length: {word_requirement}
    2. Realism: Include specific business metrics, Gartner research names, and competitor mentions.
    3. Format: Return ONLY a JSON object with keys: "type", "content", "sentiment", "key_topics", "actions_identified".
    
    Special Instructions for Format:
    - "actions_identified" must be a list of strings. If you want to include deadlines, put them in the string (e.g., "Send research report by Friday").
    - "content" must be a single string. If it's a transcript, use Marcus: ... Sofia: ...
    
    Return ONLY valid JSON.
    """
    
    system_prompt = "You are a Senior Gartner Executive Partner. Return ONLY valid JSON."
    
    llm_rotator.use_zai_fallback = True
    
    def stringify_nested(val):
        """Recursively convert nested structures to strings if they are dicts or lists"""
        if isinstance(val, dict):
            # Try to extract key info if it has fields like 'action' or 'task'
            if 'action' in val:
                return f"{val['action']} (Deadline: {val.get('deadline', 'N/A')})"
            return json.dumps(val)
        elif isinstance(val, list):
            return " | ".join([stringify_nested(i) for i in val])
        return str(val)

    try:
        content = llm_rotator.generate(prompt, system_prompt, max_tokens=6000)
        
        # Robust JSON extraction
        clean_json = None
        if "```json" in content:
            clean_json = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            clean_json = content.split("```")[1].split("```")[0].strip()
        else:
            start = content.find("{")
            end = content.rfind("}")
            if start != -1 and end != -1:
                clean_json = content[start:end+1]
        
        if not clean_json:
            print(f"DEBUG: No JSON found in content: {content[:100]}...")
            return None
            
        data = json.loads(clean_json)
        
        # Handle cases where content is a list/dictionary instead of string
        content_raw = data.get("content", "")
        if isinstance(content_raw, (list, dict)):
            content_str = stringify_nested(content_raw)
        else:
            content_str = str(content_raw)
            
        sentiment_raw = data.get("sentiment", "Neutral")
        sentiment_str = stringify_nested(sentiment_raw)
            
        actions_raw = data.get("actions_identified", [])
        if isinstance(actions_raw, list):
            actions_str_list = [stringify_nested(a) for a in actions_raw]
        else:
            actions_str_list = [stringify_nested(actions_raw)]
            
        return DetailedInteraction(
            type=data.get("type", interaction_type),
            content=content_str,
            sentiment=sentiment_str,
            key_topics=data.get("key_topics", []),
            actions_identified=actions_str_list
        )
    except Exception as e:
        print(f"ZAI Generation Error: {e}")
        return None

def main():
    with open(CLIENTS_FILE, "r") as f:
        clients = json.load(f)
    
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r") as f:
            all_interactions = json.load(f)
    else:
        all_interactions = []

    # ZAI Limit Strategy: 4 interactions per client = 100 requests. 
    # Perfectly fits the 120 req/5hr window.
    interactions_per_client = 4
    start_date = datetime(2025, 8, 1)
    end_date = datetime(2026, 2, 28)
    
    print(f"Starting ZAI-powered generation (Target: {len(clients) * interactions_per_client} total)...")
    
    interaction_id = len(all_interactions) + 5000
    
    for client in clients:
        # Check how many we already have for this client (from this batch)
        existing_count = len([i for i in all_interactions if i['client_id'] == client['id'] and i['id'].startswith("INT-5")])
        
        if existing_count >= interactions_per_client:
            print(f"Skipping {client['name']} (already has {existing_count} ZAI-grade interactions)")
            continue
            
        print(f"\nProcessing {client['name']} ({existing_count}/{interactions_per_client})...")
        
        for i in range(existing_count, interactions_per_client):
            interaction_type = random.choice(INTERACTION_TYPES)
            days_offset = random.randint(0, (end_date - start_date).days)
            interaction_date = start_date + timedelta(days=days_offset)
            
            print(f"  [{i+1}/{interactions_per_client}] Generating high-word-count {interaction_type} via ZAI...")
            
            # Add a small delay for ZAI stability
            time.sleep(1)
            
            data = generate_detailed_interaction_zai(client, interaction_type)
            
            if data and len(data.content) > 1000: # Ensure it's substantial
                record = {
                    "id": f"INT-{interaction_id}",
                    "client_id": client["id"],
                    "client_name": client["name"],
                    "date": interaction_date.strftime("%Y-%m-%d"),
                    "type": interaction_type,
                    "content": data.content,
                    "summary": data.content[:300] + "...",
                    "sentiment": data.sentiment,
                    "key_topics": data.key_topics,
                    "actions_identified": data.actions_identified
                }
                all_interactions.append(record)
                interaction_id += 1
                
                # Save after every successful ZAI call
                with open(OUTPUT_FILE, "w") as f:
                    json.dump(all_interactions, f, indent=2)
                print(f"  ✅ Saved INT-{interaction_id-1}")
            else:
                print(f"  ❌ Failed or too short. Length: {len(data.content) if data else 0}")
    
    print(f"\n✅ Phase 1.4 Pivot Complete. Total interactions: {len(all_interactions)}")

if __name__ == "__main__":
    main()

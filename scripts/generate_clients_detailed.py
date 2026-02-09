import json
import os
import random
from typing import List
from pydantic import BaseModel, Field
from gss_agent.data.llm_config import llm_rotator

DATA_DIR = "/Users/govindmittal/datascience-setup/interview_prep/gartner/gss_agent/data"
OUTPUT_FILE = os.path.join(DATA_DIR, "clients.json")

INDUSTRIES = [
    "High Tech", "Healthcare", "Finance", "Public Sector", 
    "Manufacturing", "Retail", "Supply Chain"
]

LIFECYCLE_STAGES = ["Onboarding", "Growth", "Renewal", "At Risk"]
CHURN_RISKS = ["Low", "Medium", "High"]

SUBSCRIPTION_TYPES = [
    "Gartner Standard License (GSL)",
    "Gartner for IT Leaders (GSSO)",
    "Gartner for CIOs",
    "Gartner for Finance Leaders",
    "Gartner for Supply Chain Leaders"
]

ENTITLEMENTS = [
    "Magic Quadrant Access", 
    "Analyst Inquiries", 
    "Peer Insights", 
    "Hype Cycles", 
    "Technical Professional Advice"
]

ASSOCIATES = [f"ASSOC-{i:03d}" for i in range(1, 13)]

class Contact(BaseModel):
    name: str = Field(..., description="Full name of the contact")
    role: str = Field(..., description="Job title (e.g., CIO, VP)")

class ClientProfile(BaseModel):
    company_name: str = Field(..., description="Realistic enterprise company name")
    key_contacts: List[Contact] = Field(..., description="List of 2-3 key contacts")
    industry: str = Field(..., description=f"Industry from: {INDUSTRIES}")
    region: str = Field(..., description="Region (e.g., North America, EMEA)")
    revenue: str = Field(..., description="Annual revenue (e.g., $2B)")

class ClientBatch(BaseModel):
    clients: List[ClientProfile]

def generate_client_batch(count: int = 5):
    """Generate a batch of clients using LLM with Pydantic validation"""
    prompt = f"""
    Generate {count} realistic enterprise client profiles for a Gartner Strategic Advisor system.
    Industries must be from: {INDUSTRIES}.
    Each client needs 2-3 key contacts.
    """
    
    system_prompt = "You are an expert data generator for enterprise B2B scenarios. Return ONLY valid JSON."
    
    try:
        batch = llm_rotator.generate_structured(prompt, ClientBatch, system_prompt)
        return batch.clients
    except Exception as e:
        print(f"Error generating structured client batch: {e}")
        return []

def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    
    all_clients = []
    target_count = 25
    
    print(f"Generating {target_count} clients with Pydantic validation...")
    
    while len(all_clients) < target_count:
        batch_size = min(5, target_count - len(all_clients))
        batch = generate_client_batch(batch_size)
        
        for item in batch:
            name = item.company_name
            industry = item.industry
            revenue = item.revenue
            region = item.region
            contacts = [c.model_dump() for c in item.key_contacts]
            
            client_id = f"c_{name.lower().replace(' ', '_')}_{random.randint(100, 999)}"
            
            # Enrich with random but logically consistent fields
            lifecycle = random.choice(LIFECYCLE_STAGES)
            if lifecycle == "At Risk":
                churn_risk = random.choice(["Medium", "High"])
            elif lifecycle == "Growth":
                churn_risk = random.choice(["Low", "Medium"])
            else:
                churn_risk = random.choice(CHURN_RISKS)
                
            client = {
                "id": client_id,
                "name": name,
                "industry": industry,
                "revenue": revenue,
                "region": region,
                "lifecycle_stage": lifecycle,
                "churn_risk": churn_risk,
                "subscriptions": random.sample(SUBSCRIPTION_TYPES, k=random.randint(1, 3)),
                "entitlements": random.sample(ENTITLEMENTS, k=random.randint(2, 4)),
                "key_contacts": contacts,
                "assigned_associate": random.choice(ASSOCIATES),
                "evaluation_metadata": {
                    "is_golden_client": False,
                    "target_retrieval_id": None
                }
            }
            all_clients.append(client)
            if len(all_clients) >= target_count:
                break
                
    # Label Golden Clients (10% ~ 3 clients)
    golden_indices = random.sample(range(len(all_clients)), 3)
    for idx in golden_indices:
        all_clients[idx]["evaluation_metadata"]["is_golden_client"] = True
        all_clients[idx]["evaluation_metadata"]["target_retrieval_id"] = f"GC-{idx:03d}"

    with open(OUTPUT_FILE, "w") as f:
        json.dump(all_clients, f, indent=2)
        
    print(f"Successfully generated {len(all_clients)} clients with Pydantic in {OUTPUT_FILE}")

if __name__ == "__main__":
    main()

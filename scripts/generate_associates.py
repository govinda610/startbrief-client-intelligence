import json
import os
import random

DATA_DIR = "/Users/govindmittal/datascience-setup/interview_prep/gartner/gss_agent/data"
OUTPUT_ASSOC = os.path.join(DATA_DIR, "associates.json")
OUTPUT_PERF = os.path.join(DATA_DIR, "associate_performance.json")

ASSOCIATE_NAMES = [
    "Sarah Jenkins", "David Miller", "Elena Rodriguez", "James Wilson", 
    "Aisha Khan", "Robert Chen", "Emily Davis", "Marcus Thorne",
    "Linda Wu", "Thomas Gray", "Sophia Blanco", "Kevin Lee"
]

def generate_associates():
    associates = []
    performance = []
    
    for i, name in enumerate(ASSOCIATE_NAMES):
        assoc_id = f"ASSOC-{i+1:03d}"
        
        # Associate record
        associates.append({
            "id": assoc_id,
            "name": name,
            "role": "Client Success Associate",
            "region": random.choice(["North America", "EMEA", "APAC"]),
            "tenure_months": random.randint(6, 48)
        })
        
        # Performance record
        performance.append({
            "associate_id": assoc_id,
            "metrics": {
                "cross_sell_rate": round(random.uniform(0.1, 0.4), 2),
                "upsell_rate": round(random.uniform(0.05, 0.25), 2),
                "avg_csat": round(random.uniform(3.8, 4.9), 1),
                "retention_rate": round(random.uniform(0.85, 0.98), 2),
                "avg_interaction_time_mins": random.randint(25, 55),
                "renewals_secured": random.randint(5, 20),
                "revenue_managed": random.randint(1000, 5000) * 1000
            }
        })
        
    return associates, performance

def main():
    print("Generating associate data...")
    associates, performance = generate_associates()
    
    with open(OUTPUT_ASSOC, "w") as f:
        json.dump(associates, f, indent=2)
    
    with open(OUTPUT_PERF, "w") as f:
        json.dump(performance, f, indent=2)
    
    print(f"✅ Successfully generated {len(associates)} associates and performance records.")

if __name__ == "__main__":
    main()

import json
import os
import random

DATA_DIR = "/Users/govindmittal/datascience-setup/interview_prep/gartner/gss_agent/data"
CLIENTS_FILE = os.path.join(DATA_DIR, "clients.json")
OUTPUT_FILE = os.path.join(DATA_DIR, "contracts.json")

SUBSCRIPTION_VALUES = {
    "Gartner Standard License (GSL)": 150000,
    "Gartner for IT Leaders (GSSO)": 285000,
    "Gartner for Finance Leaders": 120000,
    "Executive Programs (EXP)": 450000,
    "Gartner for Sales Leaders": 135000,
    "Gartner for Marketing Leaders": 140000
}

def generate_contracts(clients):
    contracts = []
    
    for client in clients:
        # One primary contract per client
        contract_id = f"CON-{client['id'].split('_')[-1]}"
        
        # Start date: random within last 12 months
        start_date = datetime(2025, 1, 1) + timedelta(days=random.randint(0, 300))
        end_date = start_date + timedelta(days=365)
        
        # Value based on subscriptions
        value = sum([SUBSCRIPTION_VALUES.get(s, 100000) for s in client['subscriptions']])
        
        contracts.append({
            "id": contract_id,
            "client_id": client['id'],
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "total_value": value,
            "currency": "USD",
            "status": "Active" if end_date > datetime(2026, 2, 9) else "Expired",
            "renewal_likelihood": client['churn_risk'].replace('High', 'Low').replace('Low', 'High').replace('Medium', 'Medium'),
            "service_level": "Platinum" if value > 400000 else "Gold" if value > 200000 else "Silver"
        })
        
    return contracts

from datetime import datetime, timedelta

def main():
    with open(CLIENTS_FILE, "r") as f:
        clients = json.load(f)
    
    print(f"Generating contracts for {len(clients)} clients...")
    contracts = generate_contracts(clients)
    
    with open(OUTPUT_FILE, "w") as f:
        json.dump(contracts, f, indent=2)
    
    print(f"✅ Successfully generated {len(contracts)} contracts in {OUTPUT_FILE}")

if __name__ == "__main__":
    main()

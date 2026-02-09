import json
import os
import random
from datetime import datetime, timedelta

DATA_DIR = "/Users/govindmittal/datascience-setup/interview_prep/gartner/gss_agent/data"
CLIENTS_FILE = os.path.join(DATA_DIR, "clients.json")
OUTPUT_FILE = os.path.join(DATA_DIR, "client_metrics_timeseries.json")

def generate_metrics_history(clients):
    history = []
    
    # Range: Aug 2025 - Feb 2026
    start_date = datetime(2025, 8, 1)
    
    for client in clients:
        # Determine baseline ARR and churn risk
        arr = random.randint(50, 500) * 1000 # $50k - $500k
        is_at_risk = client['churn_risk'] == 'High'
        is_growing = client['lifecycle_stage'] == 'Growth'
        
        # Monthly snapshots
        for month_idx in range(7): # 6 months + Feb
            snapshot_date = start_date + timedelta(days=month_idx * 30)
            month_str = snapshot_date.strftime("%Y-%m")
            
            # Trends
            # If at risk, engagement metrics should decline over time
            # If growing, engagement should increase
            trend_factor = (month_idx / 6.0)
            if is_at_risk:
                engagement_mult = 1.0 - (trend_factor * 0.5) # Drops by 50%
                nps_base = random.randint(3, 6)
            elif is_growing:
                engagement_mult = 1.0 + (trend_factor * 0.4) # Grows by 40%
                nps_base = random.randint(7, 10)
            else:
                engagement_mult = 1.0 + (random.uniform(-0.1, 0.1))
                nps_base = random.randint(6, 8)

            # Metrics
            logins = int(random.randint(10, 40) * engagement_mult)
            downloads = int(random.randint(5, 20) * engagement_mult)
            inquiry_util = min(100, int(random.randint(20, 80) * engagement_mult))
            nps = max(1, min(10, nps_base + random.randint(-1, 1)))
            csat = max(1, min(5, (nps / 2) + random.uniform(-0.5, 0.5)))
            
            # Contract value (stable mostly)
            if is_growing and month_idx == 4: # Upsell in month 4
                arr += 20000
            
            history.append({
                "client_id": client['id'],
                "month": month_str,
                "metrics": {
                    "login_frequency": logins,
                    "content_downloads": downloads,
                    "inquiry_utilization_pct": inquiry_util,
                    "nps": nps,
                    "csat": csat,
                    "contract_value_arr": arr,
                    "days_since_last_engagement": random.randint(1, 15) if logins > 0 else random.randint(15, 45),
                    "research_docs_accessed": downloads + random.randint(1, 10),
                    "analyst_inquiry_hours": round(inquiry_util / 10.0, 1)
                }
            })
            
    return history

def main():
    with open(CLIENTS_FILE, "r") as f:
        clients = json.load(f)
    
    print(f"Generating metrics for {len(clients)} clients...")
    metrics_data = generate_metrics_history(clients)
    
    with open(OUTPUT_FILE, "w") as f:
        json.dump(metrics_data, f, indent=2)
    
    print(f"✅ Successfully generated {len(metrics_data)} monthly metric snapshots in {OUTPUT_FILE}")

if __name__ == "__main__":
    main()

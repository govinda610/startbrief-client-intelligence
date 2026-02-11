
from langchain_core.tools import tool
import json
import logging
from typing import List, Dict, Any, Optional

# Load data with absolute paths to ensure robustness
import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

try:
    with open(os.path.join(DATA_DIR, "associates.json"), "r") as f:
        ASSOCIATES_DB = json.load(f)
    # Handle metrics file which might be large or absent
    metrics_path = os.path.join(DATA_DIR, "client_metrics_timeseries.json")
    if os.path.exists(metrics_path):
        with open(metrics_path, "r") as f:
            METRICS_DB = json.load(f)
    else:
        METRICS_DB = {}
        logging.warning("client_metrics_timeseries.json not found, using empty metrics.")

    with open(os.path.join(DATA_DIR, "clients.json"), "r") as f:
        CLIENTS_DB = json.load(f)
        
    logging.info(f"Executive Tools Loaded: {len(CLIENTS_DB)} clients, {len(ASSOCIATES_DB)} associates.")
    
except Exception as e:
    logging.error(f"Failed to load data for executive tools: {e}")
    ASSOCIATES_DB = []
    METRICS_DB = {}
    CLIENTS_DB = []

@tool
def get_all_associates_performance() -> str:
    """
    Returns a high-level summary of performance metrics for all frontline associates.
    Useful for: "Who are my top performers?", "How is the team doing?"
    """
    summary = []
    for assoc in ASSOCIATES_DB:
        # Calculate some aggregate metrics if not present
        # For now, just return what's in the DB
        summary.append({
            "name": assoc.get("name"),
            "role": assoc.get("role"),
            "focus_area": assoc.get("focus_area"),
            "client_count": len(assoc.get("assigned_clients", [])),
            # In a real system, we'd pull live performance stats here
            "status": "Active" 
        })
    return json.dumps(summary, indent=2)

@tool
def get_at_risk_clients_summary() -> str:
    """
    Identifies all clients across the entire portfolio that are showing signs of churn risk.
    Useful for: "Which clients are at risk?", "Show me the red accounts."
    """
    at_risk = []
    
    # Simple heuristic: Check latest metrics for "churn_probability" or "health_score"
    # Or rely on the static "lifecycle_stage" or "churn_risk" field in clients.json
    
    for client in CLIENTS_DB:
        risk_level = client.get("churn_risk", "Low")
        if risk_level in ["High", "Medium", "Critical"]:
             at_risk.append({
                 "client_name": client.get("name"),
                 "industry": client.get("industry"),
                 "revenue": client.get("revenue"),
                 "risk_level": risk_level,
                 "assigned_associate": client.get("assigned_associate")
             })
             
    if not at_risk:
        return "No high-risk clients identified in the current portfolio."
        
    return json.dumps(at_risk, indent=2)

@tool
def get_revenue_snapshot() -> str:
    """
    Returns a financial snapshot of the portfolio (Total ARR, Growth, etc.).
    Useful for: "What is our total ARR?", "Financial health overview."
    """
    total_arr = 0
    clients_count = len(CLIENTS_DB)
    high_value_clients = 0
    
    for client in CLIENTS_DB:
        # Heuristic: Estimate ARR based on subscriptions if not explicit
        # For now, let's mock a calculation or look for an 'arr' field
        # Assuming we don't have explicit ARR in clients.json, we'll estimate
        # $50k per subscription
        subs = len(client.get("subscriptions", []))
        estimated_val = subs * 50000
        total_arr += estimated_val
        
        if estimated_val > 100000:
            high_value_clients += 1
            
    snapshot = {
        "total_estimated_arr": f"${total_arr:,.0f}",
        "total_clients": clients_count,
        "high_value_accounts": high_value_clients,
        "average_deal_size": f"${(total_arr/clients_count if clients_count else 0):,.0f}"
    }
    return json.dumps(snapshot, indent=2)

EXECUTIVE_TOOLS = [
    get_all_associates_performance,
    get_at_risk_clients_summary,
    get_revenue_snapshot
]

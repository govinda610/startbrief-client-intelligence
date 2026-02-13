import pytest
import json
import time
from gss_agent.core.executive_tools import get_all_associates_performance, get_at_risk_clients_summary, get_revenue_snapshot

def test_revenue_snapshot_accuracy(report_engine):
    """Verify that the revenue snapshot correctly identifies portfolio health"""
    start = time.perf_counter()
    result_str = get_revenue_snapshot.invoke({})
    latency = (time.perf_counter() - start) * 1000
    result = json.loads(result_str)
    
    has_arr = "total_estimated_arr" in result
    has_clients = "total_clients" in result
    has_hva = "high_value_accounts" in result
    passed = has_arr and has_clients and has_hva
    
    report_engine.log_case("executive_tools", "ex_revenue", "Does get_revenue_snapshot return complete portfolio health data?",
        json.dumps(result, indent=2)[:600],
        "Input: (no arguments)",
        {"has_arr": has_arr, "has_clients": has_clients, "has_high_value": has_hva,
         "total_arr": result.get("total_estimated_arr", "N/A"), "total_clients": result.get("total_clients", "N/A")},
        f"{'Revenue snapshot complete with ARR, client count, and high-value accounts.' if passed else 'MISSING FIELDS — revenue aggregation logic may be broken.'}",
        latency, {}, passed)
    assert passed

def test_at_risk_clients_summary(report_engine):
    """Verify aggregation of churn risks across the portfolio"""
    start = time.perf_counter()
    result_str = get_at_risk_clients_summary.invoke({})
    latency = (time.perf_counter() - start) * 1000
    result = json.loads(result_str)
    
    is_list = isinstance(result, list)
    has_fields = True
    if is_list and len(result) > 0:
        has_fields = "client_name" in result[0] and "risk_level" in result[0]
    passed = is_list and (len(result) == 0 or has_fields)
    
    report_engine.log_case("executive_tools", "ex_risk", "Does get_at_risk_clients_summary correctly aggregate churn risks?",
        f"Found {len(result)} at-risk clients.\n{json.dumps(result[:3], indent=2) if result else '(none)'}",
        "Input: (no arguments)",
        {"at_risk_count": len(result), "has_client_name": has_fields, "has_risk_level": has_fields},
        f"{'At-risk client aggregation working correctly.' if passed else 'FAILED — check churn_risk field in clients.json and filtering logic.'}",
        latency, {}, passed)
    assert passed

def test_associates_performance_aggregation(report_engine):
    """Verify summary of associate performance"""
    start = time.perf_counter()
    result_str = get_all_associates_performance.invoke({})
    latency = (time.perf_counter() - start) * 1000
    result = json.loads(result_str)
    
    is_list = isinstance(result, list) and len(result) > 0
    associate = result[0] if is_list else {}
    has_name = "name" in associate
    has_role = "role" in associate
    has_count = "client_count" in associate
    has_status = "status" in associate
    passed = is_list and has_name and has_role and has_count and has_status
    
    report_engine.log_case("executive_tools", "ex_assoc", "Does get_all_associates_performance return valid associate summaries?",
        f"Found {len(result)} associates.\nFirst: {json.dumps(associate, indent=2)[:400]}",
        "Input: (no arguments)",
        {"associate_count": len(result), "has_name": has_name, "has_role": has_role, "has_client_count": has_count},
        f"{'Associate performance aggregation working correctly.' if passed else 'FAILED — check associates.json and performance.json linkage.'}",
        latency, {}, passed)
    assert passed

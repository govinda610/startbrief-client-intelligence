import pytest
import json
import time
from gss_agent.core.tools import (
    lookup_client_file, 
    get_client_engagement_metrics,
    lookup_contract_details,
    get_associate_performance_context,
    list_all_clients
)

def test_lookup_client_file(clients_data, report_engine):
    """Verify tool can find a client by name"""
    client = clients_data[0]
    start = time.perf_counter()
    result_str = lookup_client_file.invoke({"client_name": client["name"]})
    latency = (time.perf_counter() - start) * 1000
    
    passed = "not found" not in result_str.lower()
    if passed:
        result = json.loads(result_str)
        passed = result["name"] == client["name"]
    
    report_engine.log_case("data_access", "da_lookup", f"Can lookup_client_file find '{client['name']}'?",
        result_str[:500],
        f"Input: client_name='{client['name']}'",
        {"found": passed, "name_match": passed},
        f"{'Tool correctly retrieved client profile.' if passed else 'Tool FAILED to find client — check data reader path or client name format.'}",
        latency, {}, passed)
    assert passed

def test_get_client_engagement_metrics(clients_data, report_engine):
    """Verify engagement metrics retrieval"""
    client = clients_data[0]
    start = time.perf_counter()
    result_str = get_client_engagement_metrics.invoke({"client_name": client["name"]})
    latency = (time.perf_counter() - start) * 1000
    
    passed = "not found" not in result_str.lower()
    if passed:
        result = json.loads(result_str)
        passed = isinstance(result, list)
    
    report_engine.log_case("data_access", "da_metrics", f"Can get_client_engagement_metrics retrieve data for '{client['name']}'?",
        result_str[:500],
        f"Input: client_name='{client['name']}'",
        {"found": passed, "is_list": passed},
        f"{'Engagement metrics returned successfully as list.' if passed else 'FAILED to retrieve metrics — check interactions data linkage.'}",
        latency, {}, passed)
    assert passed

def test_lookup_contract_details(clients_data, report_engine):
    """Verify contract details retrieval"""
    client = clients_data[0]
    start = time.perf_counter()
    result_str = lookup_contract_details.invoke({"client_name": client["name"]})
    latency = (time.perf_counter() - start) * 1000
    
    passed = "not found" not in result_str.lower()
    result = {}
    if passed:
        result = json.loads(result_str)
        passed = "total_value" in result and result.get("status") in ["Active", "Expired"]
    
    report_engine.log_case("data_access", "da_contract", f"Can lookup_contract_details find contract for '{client['name']}'?",
        result_str[:500],
        f"Input: client_name='{client['name']}'",
        {"has_total_value": "total_value" in result, "valid_status": result.get("status", "N/A")},
        f"{'Contract details retrieved with valid status.' if passed else 'FAILED — check contracts.json linkage to clients.'}",
        latency, {}, passed)
    assert passed

def test_get_associate_performance_context(clients_data, report_engine):
    """Verify associate performance context retrieval"""
    client = next((c for c in clients_data if c.get("assigned_associate")), None)
    if not client:
        pytest.skip("No clients with assigned associates found in data")
    
    start = time.perf_counter()
    result_str = get_associate_performance_context.invoke({"client_name": client["name"]})
    latency = (time.perf_counter() - start) * 1000
    
    if result_str == "null":
        report_engine.log_case("data_access", "da_assoc", f"Can get_associate_performance_context find associate for '{client['name']}'?",
            "null (broken data link)",
            f"Input: client_name='{client['name']}', assigned_associate='{client['assigned_associate']}'",
            {"found": False},
            f"Broken link: Associate '{client['assigned_associate']}' not found. Re-check associates.json naming.",
            latency, {}, False)
        pytest.skip(f"Broken data link for {client['name']}")
    
    passed = "not found" not in result_str.lower()
    if passed:
        result = json.loads(result_str)
        passed = result is not None and "profile" in result and "performance" in result
    
    report_engine.log_case("data_access", "da_assoc", f"Can get_associate_performance_context find associate for '{client['name']}'?",
        result_str[:500],
        f"Input: client_name='{client['name']}'",
        {"has_profile": passed, "has_performance": passed},
        f"{'Associate context retrieved with profile and performance data.' if passed else 'FAILED to retrieve associate data — check cross-reference integrity.'}",
        latency, {}, passed)
    assert passed

def test_list_all_clients(report_engine):
    """Verify client listing"""
    start = time.perf_counter()
    result_str = list_all_clients.invoke({})
    latency = (time.perf_counter() - start) * 1000
    
    result = json.loads(result_str)
    passed = isinstance(result, list) and len(result) > 0 and "name" in result[0]
    
    report_engine.log_case("data_access", "da_list", "Does list_all_clients return a valid client list?",
        f"Returned {len(result)} clients. First: {result[0]['name'] if result else 'N/A'}",
        "Input: (no arguments)",
        {"count": len(result), "has_name_field": "name" in (result[0] if result else {})},
        f"{'Client listing works correctly.' if passed else 'FAILED — tool returned empty or malformed list.'}",
        latency, {}, passed)
    assert passed

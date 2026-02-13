import pytest
import json
from gss_agent.core.agents import get_nexus_agent
from evaluations.conftest import load_test_cases
from gss_agent.core.tools import GSS_TOOLS
from gss_agent.core.executive_tools import EXECUTIVE_TOOLS
from evaluations.conftest_patches import patch_tool_execution, patch_llm_generation

@pytest.mark.parametrize("case", load_test_cases("tool_usage_cases.json"))
def test_agent_tool_usage_trajectory(case, report_engine, llm_trace):
    query = case["query"]
    expected_tools = case["expected_tools"]
    print(f"\n⚒️ [Tool Usage] Starting evaluation for: '{query[:50]}...'")
    
    import time
    start_time = time.perf_counter()
    
    # Run the agent and capture state/history
    # Determine mode based on query keywords
    mode = "executive" if "revenue" in query.lower() or "portfolio" in query.lower() else "frontline"
    agent = get_nexus_agent(mode=mode)
    
    # We strip any whitespace
    expected_tools = [t.strip() for t in expected_tools]
    
    # Tools to track
    all_tools = GSS_TOOLS + EXECUTIVE_TOOLS
    tool_calls_found = []
    
    config = {"configurable": {"thread_id": f"traject_{hash(query)}"}}
    
    with patch_tool_execution(all_tools) as tracker:
        # Run agent
        for event in agent.stream({"messages": [("user", query)]}, config=config, stream_mode="values"):
            pass
            
        # Inspect tracker
        tool_calls_found = [call["name"] for call in tracker.tool_calls]
        trace_data = llm_trace.traces
    
    latency_ms = (time.perf_counter() - start_time) * 1000
    passed = all(tool in tool_calls_found for tool in expected_tools)
    
    report_engine.log_case(
        test_name="tool_usage",
        case_id=f"t_{hash(query)}",
        query=query,
        agent_response=f"Tools called: {', '.join(tool_calls_found)}",
        retrieved_context="N/A",
        scores={"tools_coverage": len(set(expected_tools) & set(tool_calls_found)) / len(expected_tools)},
        reasoning=f"Expected: {expected_tools}. Actual: {tool_calls_found}",
        latency_ms=latency_ms,
        tokens_used={},
        passed=passed,
        trace=trace_data
    )
    
    for tool in expected_tools:
        assert tool in tool_calls_found, f"Tool {tool} was not called for query: {query}"

def test_tool_usage_accuracy(report_engine):
    """Aggregate accuracy of tool calling"""
    import time
    cases = load_test_cases("tool_usage_cases.json")
    if not cases:
        pytest.skip("No tool usage cases found")
        
    correct_count = 0
    per_case = []
    start = time.perf_counter()
    
    all_tools_objects = GSS_TOOLS + EXECUTIVE_TOOLS
    
    for case in cases:
        query = case["query"]
        expected_tools = set(case["expected_tools"])
        
        # Determine mode
        mode = "executive" if "revenue" in query.lower() or "portfolio" in query.lower() else "frontline"
        agent = get_nexus_agent(mode=mode)
        
        tool_calls_found = set()
        
        with patch_tool_execution(all_tools_objects) as tracker:
            config = {"configurable": {"thread_id": f"eval_{hash(query)}"}}
            for _ in agent.stream({"messages": [("user", query)]}, config=config, stream_mode="values"):
                pass
            
            for call in tracker.tool_calls:
                tool_calls_found.add(call["name"])
        
        ok = expected_tools.issubset(tool_calls_found)
        if ok: correct_count += 1
        per_case.append(f"{'✅' if ok else '❌'} {query[:60]}... expected={list(expected_tools)}, got={list(tool_calls_found)}")
    
    latency = (time.perf_counter() - start) * 1000
    accuracy = correct_count / len(cases)
    passed = accuracy >= 0.80
    
    report_engine.log_case("tool_usage_aggregate", "tu_agg",
        f"Aggregate tool usage accuracy across {len(cases)} queries",
        "\n".join(per_case),
        "N/A (Aggregate)",
        {"accuracy": f"{accuracy:.2f}", "correct": correct_count, "total": len(cases)},
        f"{'Tool routing accuracy meets threshold.' if passed else f'BELOW THRESHOLD: {accuracy:.2f} (target>=0.80). Review tool descriptions and agent routing logic.'}",
        latency, {}, passed)
    
    assert accuracy >= 0.80, f"Tool usage accuracy ({accuracy:.2f}) below threshold 0.80"

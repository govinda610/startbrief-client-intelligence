import pytest
import json
from gss_agent.core.agents import supervisor_agent
from evaluations.conftest import load_test_cases

@pytest.mark.parametrize("case", load_test_cases("tool_usage_cases.json"))
def test_agent_tool_usage_trajectory(case, report_engine):
    query = case["query"]
    expected_tools = case["expected_tools"]
    print(f"\n⚒️ [Tool Usage] Starting evaluation for: '{query[:50]}...'")
    
    import time
    start_time = time.perf_counter()
    
    # Run the agent and capture state/history
    tool_calls_found = []
    config = {"configurable": {"thread_id": f"traject_{hash(query)}"}}
    
    # We use stream to capture events and identify tool calls
    for event in supervisor_agent.stream({"messages": [("user", query)]}, config=config, stream_mode="values"):
        if "messages" in event:
            last_message = event["messages"][-1]
            # Check for AI message with tool calls
            if hasattr(last_message, "tool_calls") and last_message.tool_calls:
                for tool_call in last_message.tool_calls:
                    tool_calls_found.append(tool_call["name"])
    
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
        passed=passed
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
    
    for case in cases:
        query = case["query"]
        expected_tools = set(case["expected_tools"])
        
        tool_calls_found = set()
        config = {"configurable": {"thread_id": f"eval_{hash(query)}"}}
        
        for event in supervisor_agent.stream({"messages": [("user", query)]}, config=config, stream_mode="values"):
            if "messages" in event:
                msg = event["messages"][-1]
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    for tc in msg.tool_calls:
                        tool_calls_found.add(tc["name"])
        
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

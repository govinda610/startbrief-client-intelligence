import pytest
import time
from gss_agent.core.agents import supervisor_agent
from langchain_core.messages import HumanMessage

LATENCY_CASES = [
    "Summarize health for Nexus Innovations",  # Simple lookup
    "Is TechNova Solutions at risk of churn? Analyze their 6 month metrics and recent inquiries.",  # Complex analysis
    "Who are the top 3 associates by upsell volume?",  # Calculation
]

@pytest.mark.parametrize("query", LATENCY_CASES)
def test_end_to_end_latency(query, report_engine):
    """Measures total response time using synchronous stream."""
    print(f"\n⏱️ [Latency E2E] Starting: '{query[:50]}...'")
    start_time = time.perf_counter()
    
    config = {"configurable": {"thread_id": f"lat_e2e_{hash(query)}"}}
    response_content = ""
    
    for event in supervisor_agent.stream({"messages": [HumanMessage(content=query)]}, config=config, stream_mode="values"):
        if "messages" in event:
            response_content = event["messages"][-1].content
            
    latency_ms = (time.perf_counter() - start_time) * 1000
    
    passed = latency_ms < 30000  # 30s threshold
    
    report_engine.log_case(
        test_name="latency_e2e",
        case_id=f"l_e2e_{hash(query)}",
        query=query,
        agent_response=str(response_content)[:500],
        retrieved_context="N/A",
        scores={"latency_ms": f"{latency_ms:.0f}", "threshold_ms": "30000"},
        reasoning=f"Total E2E: {latency_ms:.0f}ms. {'✅ Within 30s threshold.' if passed else f'❌ EXCEEDS 30s threshold by {(latency_ms-30000):.0f}ms. Consider optimizing retrieval or reducing tool chains.'}",
        latency_ms=latency_ms,
        tokens_used={},
        passed=passed
    )
    
    assert latency_ms < 60000, f"Latency {latency_ms:.0f}ms exceeds 60s hard cap"

@pytest.mark.parametrize("query", LATENCY_CASES[:2])
def test_ttft_latency(query, report_engine):
    """Measures Time to First Token (TTFT) using synchronous stream."""
    print(f"\n⚡ [Latency TTFT] Starting: '{query[:50]}...'")
    start_time = time.perf_counter()
    ttft_ms = None
    
    config = {"configurable": {"thread_id": f"lat_ttft_{hash(query)}"}}
    
    for event in supervisor_agent.stream({"messages": [HumanMessage(content=query)]}, config=config):
        if ttft_ms is None:
            ttft_ms = (time.perf_counter() - start_time) * 1000
            break
    
    if ttft_ms is None:
        ttft_ms = (time.perf_counter() - start_time) * 1000
    
    passed = ttft_ms < 5000  # 5s threshold
    
    report_engine.log_case(
        test_name="latency_ttft",
        case_id=f"l_ttft_{hash(query)}",
        query=query,
        agent_response="[TTFT Measurement]",
        retrieved_context="N/A",
        scores={"ttft_ms": f"{ttft_ms:.0f}", "threshold_ms": "5000"},
        reasoning=f"First token in {ttft_ms:.0f}ms. {'✅ Within 5s threshold.' if passed else f'❌ SLOW: {ttft_ms:.0f}ms > 5s. Consider model warm-up or caching.'}",
        latency_ms=ttft_ms,
        tokens_used={},
        passed=passed
    )
    
    assert ttft_ms < 10000, f"TTFT {ttft_ms:.0f}ms exceeds 10s hard cap"

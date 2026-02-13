import pytest
import json
from gss_agent.core.agents import supervisor_agent, llm
from evaluations.conftest import load_test_cases

JUDGE_PROMPT = """You are an expert AI performance auditor. 
Evaluate the following interaction between a user and a Strategic Advisor Agent.

User Query: {query}
Agent Response: {response}

Rubric (Rate 1-5):
1. RELEVANCE: Does it answer the user's specific question?
2. ACCURACY: Does it avoid hallucinations and use provided context correctly?
3. COMPLETENESS: Does it provide specialized talking points or business metrics?
4. TONE: Is it professional and strategic?

Also identify if there is any HALLUCINATION (Yes/No).

Return ONLY a JSON object:
{{
  "relevance": int,
  "accuracy": int,
  "completeness": int,
  "tone": int,
  "hallucination": "Yes" | "No",
  "reasoning": "string"
}}
"""

@pytest.mark.parametrize("case", load_test_cases("response_quality_cases.json"))
def test_response_quality_llm_judge(case, report_engine):
    query = case["query"]
    print(f"\n⚖️ [Quality Judge] Starting evaluation for: '{query[:50]}...'")
    
    # Get agent response
    import time
    start_time = time.perf_counter()
    print(f"   - [Quality] Invoking Agent for query: '{query[:40]}...'")
    config = {"configurable": {"thread_id": f"judge_{hash(query)}"}}
    response_msg = supervisor_agent.invoke({"messages": [("user", query)]}, config=config)
    agent_response = response_msg["messages"][-1].content
    
    print("   - [Quality] Invoking Quality LLM Judge...")
    # Judge the response
    prompt = JUDGE_PROMPT.format(query=query, response=agent_response)
    judge_result = llm.invoke(prompt)
    
    latency_ms = (time.perf_counter() - start_time) * 1000
    usage = judge_result.response_metadata.get("usage", {})
    
    # Parse judge result
    try:
        print("   - [Quality] Parsing Quality JSON response...")
        clean_content = judge_result.content.strip()
        if "```json" in clean_content:
            clean_content = clean_content.split("```json")[1].split("```")[0].strip()
        elif "```" in clean_content:
            clean_content = clean_content.split("```")[1].split("```")[0].strip()
            
        scores = json.loads(clean_content)
        
        avg_score = (scores["relevance"] + scores["accuracy"] + scores["completeness"] + scores["tone"]) / 4
        passed = (scores["hallucination"] == "No") and (avg_score >= 3.5)
        
        report_engine.log_case(
            test_name="response_quality",
            case_id=f"q_{hash(query)}",
            query=query,
            agent_response=agent_response,
            retrieved_context="N/A (Reference-Free)",
            scores=scores,
            reasoning=scores.get("reasoning", ""),
            latency_ms=latency_ms,
            tokens_used=usage,
            passed=passed
        )
        
        assert scores["hallucination"] == "No", f"Hallucination detected for query: {query}. Reasoning: {scores.get('reasoning')}"
        assert avg_score >= 3.5, f"Average score {avg_score:.2f} below threshold 3.5 for query: {query}"
        
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        report_engine.log_case(
            test_name="response_quality", case_id=f"q_{hash(query)}", query=query,
            agent_response=agent_response, retrieved_context="N/A",
            scores={"parse_error": True}, reasoning=f"Judge output parsing failed: {e}",
            latency_ms=latency_ms, tokens_used=usage, passed=False
        )
        pytest.fail(f"Failed to parse judge output: {e}\nOutput: {judge_result.content}")
    except AssertionError:
        raise
    except Exception as e:
        pytest.fail(f"Unexpected error during evaluation: {e}")

def test_aggregate_quality_metrics(report_engine):
    """Verify average quality across all cases"""
    import time
    cases = load_test_cases("response_quality_cases.json")
    if not cases:
        pytest.skip("No response quality cases found")
        
    all_avg_scores = []
    hallu_count = 0
    start = time.perf_counter()
    
    for case in cases:
        query = case["query"]
        config = {"configurable": {"thread_id": f"agg_judge_{hash(query)}"}}
        resp = supervisor_agent.invoke({"messages": [("user", query)]}, config=config)
        agent_resp = resp["messages"][-1].content
        
        judge_prompt = JUDGE_PROMPT.format(query=query, response=agent_resp)
        judge_resp = llm.invoke(judge_prompt)
        
        try:
            clean_content = judge_resp.content.strip()
            if "```json" in clean_content: clean_content = clean_content.split("```json")[1].split("```")[0].strip()
            scores = json.loads(clean_content)
            
            avg = (scores["relevance"] + scores["accuracy"] + scores["completeness"] + scores["tone"]) / 4
            all_avg_scores.append(avg)
            if scores["hallucination"] == "Yes": hallu_count += 1
        except:
            continue
    
    latency = (time.perf_counter() - start) * 1000
    
    if not all_avg_scores:
        report_engine.log_case("response_quality_aggregate", "rq_agg", "Aggregate quality across all response cases",
            "FAILED: No valid evaluation results were parsed.", "N/A", {}, "All LLM judge responses failed to parse.", latency, {}, False)
        pytest.fail("No valid evaluation results were parsed")
        
    final_avg = sum(all_avg_scores) / len(all_avg_scores)
    hallu_rate = hallu_count / len(all_avg_scores)
    passed = final_avg >= 3.8 and hallu_rate <= 0.15
    
    report_engine.log_case("response_quality_aggregate", "rq_agg",
        f"Aggregate response quality across {len(cases)} test cases",
        f"Final Avg Score: {final_avg:.2f}\nHallucination Rate: {hallu_rate:.2f} ({hallu_count}/{len(all_avg_scores)})\nPer-case averages: {[f'{s:.1f}' for s in all_avg_scores]}",
        "N/A (Aggregate)",
        {"final_avg_score": f"{final_avg:.2f}", "hallucination_rate": f"{hallu_rate:.2f}", "cases_evaluated": len(all_avg_scores)},
        f"{'Quality and hallucination thresholds met.' if passed else f'ISSUES: Avg={final_avg:.2f} (target>=3.8), Hallucination={hallu_rate:.2f} (target<=0.15). Improve prompts and retrieval grounding.'}",
        latency, {}, passed)
    
    assert final_avg >= 3.8, f"Final average score ({final_avg:.2f}) below 3.8"
    assert hallu_rate <= 0.15, f"Hallucination rate ({hallu_rate:.2f}) above 15%"

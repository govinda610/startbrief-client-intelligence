import pytest
import json
import time
from gss_agent.core.agents import supervisor_agent, llm
from evaluations.conftest import load_test_cases

RELEVANCY_PROMPT = """You are an expert AI quality auditor.
Evaluate the RELEVANCY of the AI response to the user query.

User Query: {query}
Agent Response: {response}

Rubric:
- Score 5: Directly and comprehensively answer the question. Professional and focused.
- Score 4: Answers correctly but contains minor irrelevant details or slight formatting issues.
- Score 3: Mostly relevant but misses a key sub-point or provides redundant info.
- Score 2: Partially addresses the query but misses the main point or is overly generic.
- Score 1: Completely off-topic or irrelevant.

Return ONLY a JSON object:
{{
  "relevancy_score": int (1-5),
  "missing_aspects": ["string"],
  "reasoning": "string"
}}
"""

@pytest.mark.parametrize("case", load_test_cases("response_quality_cases.json"))
def test_answer_relevancy_metric(case, report_engine):
    query = case["query"]
    print(f"\n🎯 [Relevancy] Starting evaluation for: '{query[:50]}...'")
    
    start_time = time.perf_counter()
    config = {"configurable": {"thread_id": f"rel_{hash(query)}"}}
    
    print(f"   - [Relevancy] Invoking Agent for query: '{query[:40]}...'")
    res = supervisor_agent.invoke({"messages": [("user", query)]}, config=config)
    agent_response = res["messages"][-1].content
    
    print("   - [Relevancy] Invoking Relevancy LLM Judge...")
    prompt = RELEVANCY_PROMPT.format(query=query, response=agent_response)
    judge_res = llm.invoke(prompt)
    
    latency_ms = (time.perf_counter() - start_time) * 1000
    usage = judge_res.response_metadata.get("usage", {})
    
    # Parse and Log
    try:
        print("   - [Relevancy] Parsing Relevancy JSON response...")
        clean_content = judge_res.content.strip()
        if "```json" in clean_content:
            clean_content = clean_content.split("```json")[1].split("```")[0].strip()
        
        eval_data = json.loads(clean_content)
        passed = eval_data["relevancy_score"] >= 4
        
        report_engine.log_case(
            test_name="answer_relevancy",
            case_id=f"r_{hash(query)}",
            query=query,
            agent_response=agent_response,
            retrieved_context="N/A (Reference-Free)",
            scores={"relevancy": eval_data["relevancy_score"]},
            reasoning=eval_data["reasoning"],
            latency_ms=latency_ms,
            tokens_used=usage,
            passed=passed,
            metadata={"missing_aspects": eval_data.get("missing_aspects", [])}
        )
        
        assert passed, f"Relevancy score {eval_data['relevancy_score']} below 4. Reasoning: {eval_data['reasoning']}"
        
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        report_engine.log_case(
            test_name="answer_relevancy", case_id=f"r_{hash(query)}", query=query,
            agent_response=agent_response, retrieved_context="N/A",
            scores={"relevancy": "PARSE_ERROR"}, reasoning=f"Judge output parsing failed: {e}",
            latency_ms=latency_ms, tokens_used=usage, passed=False
        )
        pytest.fail(f"LLM Judge response parsing/format error: {e}")
    except AssertionError:
        raise
    except Exception as e:
        pytest.fail(f"Unexpected error during evaluation: {e}")

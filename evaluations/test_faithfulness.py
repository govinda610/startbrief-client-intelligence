import pytest
import json
import time
from gss_agent.core.agents import supervisor_agent, llm
from evaluations.conftest import load_test_cases

FAITHFULNESS_PROMPT = """You are an expert fact-checker.
Your task is to evaluate the FAITHFULNESS of an AI response to a provided context.

Context (data the agent retrieved via its tools):
{context}

Response (final answer the agent gave):
{response}

Instructions:
1. Extract the core factual claims made in the response.
2. For each claim, check if it is directly supported by the context.
3. Calculate faithfulness: (Number of supported claims) / (Total number of claims).
4. Identify any specific claims that are NOT supported (hallucinations).

Return ONLY a JSON object:
{{
  "claims": [
    {{
      "claim": "string",
      "supported": true | false,
      "evidence": "string or 'none'"
    }}
  ],
  "faithfulness_score": float (0.0 to 1.0),
  "reasoning": "string"
}}
"""

@pytest.mark.parametrize("case", load_test_cases("response_quality_cases.json"))
def test_faithfulness_metric(case, report_engine):
    query = case["query"]
    print(f"\n🔍 [Faithfulness] Starting evaluation for: '{query[:50]}...'")
    
    start_time = time.perf_counter()
    config = {"configurable": {"thread_id": f"faith_{hash(query)}"}}
    
    # 1. Run agent and capture FULL message history
    print(f"   - [Faithfulness] Invoking Agent for query: '{query[:40]}...'")
    res = supervisor_agent.invoke({"messages": [("user", query)]}, config=config)
    agent_response = res["messages"][-1].content
    
    # 2. Extract ACTUAL context from agent's tool call outputs
    #    This is the data the agent really used — not a separate vector store query
    print("   - [Faithfulness] Extracting context from agent's tool call outputs...")
    tool_outputs = []
    for msg in res["messages"]:
        if hasattr(msg, "type") and msg.type == "tool":
            tool_outputs.append(msg.content)
    
    context = "\n---\n".join(tool_outputs) if tool_outputs else "No tool context captured."
    print(f"   - [Faithfulness] Captured {len(tool_outputs)} tool outputs as context")
    
    # 3. Judge Faithfulness using ACTUAL context
    print("   - [Faithfulness] Invoking Fact-Checker LLM Judge...")
    prompt = FAITHFULNESS_PROMPT.format(context=context, response=agent_response)
    judge_res = llm.invoke(prompt)
    
    latency_ms = (time.perf_counter() - start_time) * 1000
    usage = judge_res.response_metadata.get("usage", {})
    
    # 4. Parse and Log
    try:
        print("   - [Faithfulness] Parsing Fact-Checker JSON response...")
        clean_content = judge_res.content.strip()
        if "```json" in clean_content:
            clean_content = clean_content.split("```json")[1].split("```")[0].strip()
        
        eval_data = json.loads(clean_content)
        passed = eval_data["faithfulness_score"] >= 0.8
        
        report_engine.log_case(
            test_name="faithfulness",
            case_id=f"f_{hash(query)}",
            query=query,
            agent_response=agent_response,
            retrieved_context=context[:2000],  # Truncate for report readability
            scores={"faithfulness": eval_data["faithfulness_score"]},
            reasoning=eval_data["reasoning"],
            latency_ms=latency_ms,
            tokens_used=usage,
            passed=passed,
            metadata={"claims": eval_data.get("claims", []), "num_tool_outputs": len(tool_outputs)}
        )
        
        assert passed, f"Faithfulness score {eval_data['faithfulness_score']} below 0.8. Reasoning: {eval_data['reasoning']}"
        
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        report_engine.log_case(
            test_name="faithfulness", case_id=f"f_{hash(query)}", query=query,
            agent_response=agent_response, retrieved_context=context[:500],
            scores={"faithfulness": "PARSE_ERROR"}, reasoning=f"Judge output parsing failed: {e}",
            latency_ms=latency_ms, tokens_used=usage, passed=False
        )
        pytest.fail(f"LLM Judge response parsing/format error: {e}")
    except AssertionError:
        raise
    except Exception as e:
        report_engine.log_case(
            test_name="faithfulness", case_id=f"f_{hash(query)}", query=query,
            agent_response=str(agent_response)[:500] if 'agent_response' in dir() else "N/A",
            retrieved_context="N/A", scores={"faithfulness": "ERROR"},
            reasoning=f"Unexpected error: {e}", latency_ms=latency_ms if 'latency_ms' in dir() else 0,
            tokens_used={}, passed=False
        )
        pytest.fail(f"Unexpected error during evaluation: {e}")

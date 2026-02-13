import pytest
import json
import time
from gss_agent.core.agents import supervisor_agent, llm
from evaluations.conftest import load_test_cases
from gss_agent.rag.vector_store import NexusVectorStore

CONTEXT_PRECISION_PROMPT = """You are a RAG performance auditor.
Evaluate the usefulness of the retrieved context for answering the specific user query.

Query: {query}
Response: {response}
Context Chunk: {chunk}

Was this chunk useful for providing the information found in the response?
Respond ONLY with a JSON object:
{{
  "useful": true | false,
  "reasoning": "string"
}}
"""

@pytest.mark.parametrize("case", load_test_cases("retrieval_cases.json"))
def test_context_precision_metric(case, report_engine):
    query = case["query"]
    print(f"\n📍 [Precision] Starting evaluation for: '{query[:50]}...'")
    
    start_time = time.perf_counter()
    
    # 1. Run Retrieval
    print("   - [Precision] Querying vector store for context chunks...")
    vs = NexusVectorStore()
    if case["category"] == "research":
        results = vs.search_research(query, n_results=3)
    else:
        results = vs.search_interactions(query, n_results=3)
        
    chunks = results["documents"][0] if results["documents"] else []
    if not chunks:
        pytest.skip("No chunks retrieved for this case")
    print(f"   - [Precision] Retrieved {len(chunks)} chunks")
        
    # 2. Get Agent Response
    print(f"   - [Precision] Invoking Agent for query: '{query[:40]}...'")
    config = {"configurable": {"thread_id": f"prec_{hash(query)}"}}
    res = supervisor_agent.invoke({"messages": [("user", query)]}, config=config)
    agent_response = res["messages"][-1].content
    
    # 3. Judge each chunk
    useful_count = 0
    reasons = []
    
    for i, chunk in enumerate(chunks):
        print(f"   - [Precision] Judging chunk {i+1}/{len(chunks)}...")
        prompt = CONTEXT_PRECISION_PROMPT.format(query=query, response=agent_response, chunk=chunk)
        judge_res = llm.invoke(prompt)
        
        try:
            clean = judge_res.content.strip()
            if "```json" in clean: clean = clean.split("```json")[1].split("```")[0].strip()
            eval_data = json.loads(clean)
            if eval_data["useful"]:
                useful_count += 1
            reasons.append(f"Chunk {i+1}: {'useful' if eval_data['useful'] else 'not useful'} - {eval_data['reasoning']}")
        except Exception as e:
            reasons.append(f"Chunk {i+1}: parse error - {e}")
            continue
            
    precision = useful_count / len(chunks) if chunks else 0
    latency_ms = (time.perf_counter() - start_time) * 1000
    
    passed = precision >= 0.5
    print(f"   - [Precision] Result: {useful_count}/{len(chunks)} useful chunks (precision={precision:.2f})")
    
    # 4. Log
    report_engine.log_case(
        test_name="context_precision",
        case_id=f"p_{hash(query)}",
        query=query,
        agent_response=agent_response,
        retrieved_context="\n---\n".join([c[:300] for c in chunks]),
        scores={"context_precision": precision, "useful_chunks": useful_count, "total_chunks": len(chunks)},
        reasoning="; ".join(reasons),
        latency_ms=latency_ms,
        tokens_used={"note": "aggregated chunks"},
        passed=passed
    )
    
    assert precision >= 0.5, f"Context precision {precision:.2f} below threshold 0.5"

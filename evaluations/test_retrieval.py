import pytest
import json
import os
from evaluations.conftest import load_test_cases

def calculate_recall_at_k(retrieved_ids, expected_ids, k=5):
    """Calculate Recall@K: Proportion of relevant items retrieved in top K"""
    if not expected_ids:
        return 1.0
    retrieved_at_k = set(retrieved_ids[:k])
    relevant_retrieved = retrieved_at_k.intersection(set(expected_ids))
    return len(relevant_retrieved) / len(expected_ids)

def calculate_mrr(retrieved_ids, expected_ids):
    """Calculate Mean Reciprocal Rank: inverse of the rank of the first relevant item"""
    for i, rid in enumerate(retrieved_ids):
        if rid in expected_ids:
            return 1.0 / (i + 1)
    return 0.0

@pytest.mark.parametrize("case", load_test_cases("retrieval_cases.json"))
def test_recall_and_mrr(vector_store, case, report_engine):
    query = case["query"]
    expected_ids = case["expected_doc_ids"]
    category = case["category"]
    print(f"\n🔎 [Retrieval] Starting: '{query[:50]}...' (category={category})")
    
    import time
    start_time = time.perf_counter()
    
    # Perform search based on category
    if category == "research":
        results = vector_store.search_research(query, n_results=10)
    else:
        results = vector_store.search_interactions(query, n_results=10)
        
    latency_ms = (time.perf_counter() - start_time) * 1000
    retrieved_ids = results["ids"][0] if results["ids"] else []
    
    recall_5 = calculate_recall_at_k(retrieved_ids, expected_ids, k=5)
    mrr = calculate_mrr(retrieved_ids, expected_ids)
    
    passed = recall_5 > 0 and mrr > 0
    
    report_engine.log_case(
        test_name="retrieval",
        case_id=f"ret_{hash(query)}",
        query=query,
        agent_response=f"Retrieved IDs: {', '.join(retrieved_ids[:5])}",
        retrieved_context="N/A (Individual Case)",
        scores={"recall@5": recall_5, "mrr": mrr},
        reasoning=f"Expected: {expected_ids}. Top 3: {retrieved_ids[:3]}",
        latency_ms=latency_ms,
        tokens_used={},
        passed=passed
    )
    
    assert mrr > 0, f"No expected documents found in top 10 for query: {query}"
    assert recall_5 > 0, f"Zero recall@5 for query: {query}"

def test_aggregate_retrieval_metrics(vector_store, report_engine):
    """Verify aggregate thresholds across all cases"""
    import time
    cases = load_test_cases("retrieval_cases.json")
    if not cases:
        pytest.skip("No retrieval cases found")
        
    recalls = []
    mrrs = []
    start = time.perf_counter()
    
    for case in cases:
        if case["category"] == "research":
            results = vector_store.search_research(case["query"], n_results=10)
        else:
            results = vector_store.search_interactions(case["query"], n_results=10)
            
        retrieved_ids = results["ids"][0] if results["ids"] else []
        recalls.append(calculate_recall_at_k(retrieved_ids, case["expected_doc_ids"], k=5))
        mrrs.append(calculate_mrr(retrieved_ids, case["expected_doc_ids"]))
    
    latency = (time.perf_counter() - start) * 1000
    avg_recall = sum(recalls) / len(recalls)
    avg_mrr = sum(mrrs) / len(mrrs)
    passed = avg_recall >= 0.60 and avg_mrr >= 0.50
    
    report_engine.log_case("retrieval_aggregate", "ret_agg",
        f"Aggregate retrieval metrics across {len(cases)} queries",
        f"Avg Recall@5: {avg_recall:.2f}\nAvg MRR: {avg_mrr:.2f}\nPer-case Recall: {[f'{r:.2f}' for r in recalls]}\nPer-case MRR: {[f'{m:.2f}' for m in mrrs]}",
        "N/A (Aggregate)",
        {"avg_recall@5": f"{avg_recall:.2f}", "avg_mrr": f"{avg_mrr:.2f}", "cases": len(cases)},
        f"{'Retrieval quality meets both thresholds.' if passed else f'BELOW THRESHOLD: Recall@5={avg_recall:.2f} (target>=0.60), MRR={avg_mrr:.2f} (target>=0.50). Improve embeddings or chunk strategy.'}",
        latency, {}, passed)
    
    assert avg_recall >= 0.60, f"Average Recall@5 ({avg_recall:.2f}) below threshold 0.60"
    assert avg_mrr >= 0.50, f"Average MRR ({avg_mrr:.2f}) below threshold 0.50"

import pytest
import json
import os

def test_interaction_counts(interactions_data, report_engine):
    """Verify total interaction count is within expected range"""
    count = len(interactions_data)
    passed = count >= 200
    report_engine.log_case("data_quality", "dq_count", "Total interaction count >= 200?",
        f"Found {count} interactions in the dataset.",
        "N/A", {"count": count}, 
        f"{'Sufficient' if passed else 'INSUFFICIENT'} data volume. Target: 200, Actual: {count}.",
        0, {}, passed)
    assert passed, f"Expected at least 200 interactions, found {count}"

def test_no_empty_content(interactions_data, report_engine):
    """Verify no interaction has empty content (Fix for Batch 1 issues)"""
    empty = [i["id"] for i in interactions_data if not i.get("content", "").strip()]
    passed = len(empty) == 0
    report_engine.log_case("data_quality", "dq_empty", "Are there any interactions with empty content?",
        f"{'No empty interactions found.' if passed else f'Found {len(empty)} empty interactions: {empty[:5]}'}",
        "N/A", {"empty_count": len(empty)},
        f"{'All interactions have substantive content.' if passed else f'Empty records need regeneration. IDs: {empty}'}",
        0, {}, passed)
    assert passed, f"Found interactions with empty content: {empty}"

def test_word_counts(interactions_data, report_engine):
    """Verify content quality via word count averages"""
    by_type = {}
    for i in interactions_data:
        t = i["type"]
        if t not in by_type: by_type[t] = []
        by_type[t].append(len(i.get("content", "").split()))
    
    thresholds = {
        "Phone Call Transcript": 800,
        "Analyst Inquiry Call": 700,
        "Email Thread": 500,
        "Meeting Note": 400,
        "Support Ticket": 250
    }
    
    results = []
    all_pass = True
    for t, min_avg in thresholds.items():
        if t in by_type:
            avg = sum(by_type[t]) / len(by_type[t])
            ok = avg >= min_avg
            if not ok: all_pass = False
            results.append(f"{t}: avg={avg:.0f} (threshold={min_avg}) {'✅' if ok else '❌'}")
    
    report_engine.log_case("data_quality", "dq_words", "Do all interaction types meet minimum word count thresholds?",
        "\n".join(results),
        "N/A", {t: f"{sum(by_type.get(t,[0]))/max(len(by_type.get(t,[1])),1):.0f}" for t in thresholds if t in by_type},
        f"{'All types meet thresholds.' if all_pass else 'Some types have low word counts — consider regenerating data with longer prompts.'}",
        0, {}, all_pass)
    
    for t, min_avg in thresholds.items():
        if t in by_type:
            avg = sum(by_type[t]) / len(by_type[t])
            assert avg >= min_avg, f"Average word count for {t} ({avg:.1f}) is below threshold {min_avg}"

def test_sentiment_labels(interactions_data, report_engine):
    """Verify we have at least 50 'true_sentiment' labels for NLP evaluation"""
    labeled = [i for i in interactions_data if "true_sentiment" in i]
    passed = len(labeled) >= 50
    report_engine.log_case("data_quality", "dq_sentiment", "Are there >= 50 true_sentiment labels for NLP eval?",
        f"Found {len(labeled)} labeled interactions out of {len(interactions_data)} total.",
        "N/A", {"labeled": len(labeled), "total": len(interactions_data), "pct": f"{len(labeled)/len(interactions_data)*100:.1f}%"},
        f"{'Sufficient labels for sentiment model evaluation.' if passed else 'Need more labeled data. Run labeling script again.'}",
        0, {}, passed)
    assert passed, f"Need at least 50 true_sentiment labels, found {len(labeled)}"

def test_client_consistency(clients_data, interactions_data, report_engine):
    """Verify all interactions map to valid clients"""
    client_ids = {c["id"] for c in clients_data}
    orphans = [i["id"] for i in interactions_data if i["client_id"] not in client_ids]
    passed = len(orphans) == 0
    report_engine.log_case("data_quality", "dq_client_ref", "Do all interactions reference valid client IDs?",
        f"{'All {len(interactions_data)} interactions map to valid clients.' if passed else f'Found {len(orphans)} orphaned interactions: {orphans[:5]}'}",
        f"Client IDs in dataset: {len(client_ids)}",
        {"orphaned": len(orphans), "total_interactions": len(interactions_data)},
        f"{'Cross-reference integrity is intact.' if passed else 'Data integrity broken — orphaned interactions need client_id correction.'}",
        0, {}, passed)
    assert passed, f"Found orphaned interactions: {orphans}"

def test_required_fields(clients_data, interactions_data, content_data, report_engine):
    """Verify core structural integrity"""
    missing = []
    for c in clients_data:
        for field in ["id", "name", "industry", "revenue", "churn_risk", "assigned_associate"]:
            if field not in c:
                missing.append(f"Client {c.get('id','?')} missing '{field}'")
    for i in interactions_data:
        for field in ["id", "client_id", "type", "content", "sentiment", "date"]:
            if field not in i:
                missing.append(f"Interaction {i.get('id','?')} missing '{field}'")
    for r in content_data:
        for field in ["id", "title", "abstract", "strategic_value"]:
            if field not in r:
                missing.append(f"Research {r.get('id','?')} missing '{field}'")
    
    passed = len(missing) == 0
    report_engine.log_case("data_quality", "dq_fields", "Do all records have required fields?",
        f"{'All records have required fields.' if passed else chr(10).join(missing[:10])}",
        f"Checked: {len(clients_data)} clients, {len(interactions_data)} interactions, {len(content_data)} content items",
        {"missing_count": len(missing)},
        f"{'Schema integrity verified across all data files.' if passed else f'{len(missing)} missing fields — data generation scripts need field validation.'}",
        0, {}, passed)
    assert passed, f"Missing fields found: {missing}"

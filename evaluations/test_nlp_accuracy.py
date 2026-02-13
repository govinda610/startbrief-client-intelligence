import pytest
import os
import json

from evaluations.conftest import load_test_cases

# Skip torch/transformers on Apple Silicon to avoid Bus Error
# Instead, use a mock accuracy test based on our sentiment labels
# The real DistilBERT test can be run in CI/CD with adequate memory

def test_distilbert_accuracy(interactions_data, report_engine):
    """
    Evaluate real DistilBERT sentiment accuracy.
    Using explicit loader to bypass Bus Errors on Mac.
    """
    import os
    import torch
    from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
    
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    torch.set_num_threads(1)
    
    labeled_data = [i for i in interactions_data if i.get("true_sentiment") in ["Positive", "Negative"]]
    if not labeled_data:
        pytest.skip("No labeled data (Positive/Negative) found.")
    
    model_name = "distilbert-base-uncased-finetuned-sst-2-english"
    print(f"   - [NLP] Explicitly loading {model_name}...")
    
    # Load model and tokenizer explicitly to control resource usage
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(
        model_name,
        low_cpu_mem_usage=False, # Crucial: avoid mmap which causes SIGBUS on some Macs
        device_map=None # Force CPU
    )
    
    classifier = pipeline("sentiment-analysis", model=model, tokenizer=tokenizer)
    
    y_true = [item["true_sentiment"].upper() for item in labeled_data]
    y_pred = []
    mismatches = []
    
    for i, item in enumerate(labeled_data):
        content = item["content"][:512]
        result = classifier(content)[0]
        pred = result["label"].upper() # 'POSITIVE' or 'NEGATIVE'
        y_pred.append(pred)
        
        if pred != y_true[i]:
            mismatches.append({
                "id": item["id"], 
                "true": y_true[i], 
                "pred": pred, 
                "score": f"{result['score']:.2f}",
                "snippet": content[:80]
            })
    
    accuracy = sum(1 for t, p in zip(y_true, y_pred) if t == p) / len(y_true)
    passed = accuracy >= 0.75  # Higher threshold for real model
    
    mismatch_detail = "\n".join([
        f"  - {m['id']}: true={m['true']}, pred={m['pred']} (conf:{m['score']}) → \"{m['snippet']}...\"" 
        for m in mismatches[:5]
    ])
    
    report_engine.log_case("nlp_accuracy", "nlp_distilbert",
        f"DistilBERT Sentiment Accuracy (N={len(y_true)})",
        f"Accuracy: {accuracy:.2f} ({sum(1 for t, p in zip(y_true, y_pred) if t == p)}/{len(y_true)})\n\nMismatches:\n{mismatch_detail}",
        "DistilBERT (distilbert-base-uncased-finetuned-sst-2-english)",
        {"accuracy": f"{accuracy:.2f}", "correct": sum(1 for t, p in zip(y_true, y_pred) if t == p), "total": len(y_true)},
        f"{'Model performance meets production thresholds.' if passed else 'Model accuracy below 0.75. Review data quality or consider fine-tuning.'}",
        0, {}, passed)
    
    assert passed, f"DistilBERT accuracy {accuracy:.2f} is below target 0.75"

def test_sentiment_distribution(interactions_data, report_engine):
    """Ensure data has a healthy mix of sentiments for robust evaluation"""
    sentiments = [i["sentiment"] for i in interactions_data]
    counts = {s: sentiments.count(s) for s in set(sentiments)}
    total = len(sentiments)
    
    results = []
    all_pass = True
    for s in ["Positive", "Negative", "Neutral"]:
        ratio = counts.get(s, 0) / total
        ok = ratio >= 0.05
        if not ok: all_pass = False
        results.append(f"{s}: {counts.get(s, 0)} ({ratio:.1%}) {'✅' if ok else '❌'}")
    
    report_engine.log_case("nlp_accuracy", "nlp_distribution",
        "Is sentiment distribution balanced? (each class >= 5%)",
        "\n".join(results),
        f"Total: {total} interactions",
        counts,
        f"{'Healthy sentiment distribution across all classes.' if all_pass else 'Imbalanced distribution — some sentiment classes are under-represented. Consider rebalancing data generation.'}",
        0, {}, all_pass)
    
    for s in ["Positive", "Negative", "Neutral"]:
        ratio = counts.get(s, 0) / total
        assert ratio >= 0.05, f"Sentiment class {s} is under-represented ({ratio:.2f})"

# 🩺 Nexus Evaluation Suite

The Nexus Strategic Advisor includes a sophisticated evaluation system for continuous improvement and quality assurance. This suite provides "white-box" visibility into agent reasoning and benchmarks performance across multiple dimensions.

## 📊 Core Metrics

| Dimension | Metrics | Methodology | Threshold |
|:---|:---|:---|:---|
| **Response Quality** | Accuracy, Tone, Completeness | LLM-as-Judge (1-5) | Avg ≥ 3.5 |
| **Groundedness** | Faithfulness, Hallucination Check | Fact-grounding (RAGAS-style) | Score ≥ 0.8 |
| **Operational** | E2E Latency, TTFT | Middleware Instrumentation | E2E ≤ 30s |
| **Technical** | Context Precision, Tool Usage | Trajectory Matching | Precision ≥ 0.5 |

## 🔬 Methodology

### RAGAS-Style Evaluation
We implement the **RAGAS (Retrieval-Augmented Generation Evaluation)** methodology via custom LLM-as-Judge prompts:
- **Faithfulness**: Verifies that every claim in the response is grounded in the retrieved documents.
- **Answer Relevancy**: Measures how directly the response addresses the user's specific query.
- **Context Precision**: Evaluates the usefulness of individual retrieved chunks from the vector store.

### Trace Capture
The system intercepts every LLM call across the entire agent graph (Supervisor, ClientIntel, ContentMatch, Critic), capturing:
- **Inputs**: The exact prompt sent to the LLM.
- **Reasoning**: The internal "thought" process or tool calls.
- **Outputs**: The final response or tool output.

## 🚀 Running Evaluations

### 1. Run the Full Suite
Execute all test suites and generate a consolidated report:
```bash
python evaluations/run_all.py
```

### 2. View Results
Reports are saved in `evaluations/results/` as:
- **JSON**: Machine-readable data for trend analysis.
- **HTML**: Rich interactive dashboard with collapsible reasoning traces.

### 3. Individual Test Suites
You can run specific dimensions independently:
- **Data Quality**: `pytest evaluations/test_data_quality.py`
- **NLP Accuracy**: `pytest evaluations/test_nlp_accuracy.py`
- **Faithfulness**: `pytest evaluations/test_faithfulness.py`
- **Latency**: `pytest evaluations/test_latency.py`

## 🛠️ Configuration
- **Model**: LLM-as-Judge uses `glm-4.7` via the ZAI API.
- **Checkpoints**: Traces are captured via `conftest_patches.py` which wraps `langchain` generation events.

import subprocess
import os
import time

def run_suite(name, cmd):
    print(f"\n{'='*60}")
    print(f"🚀 STARTING SUITE: {name}")
    print(f"{'='*60}")
    start = time.perf_counter()
    result = subprocess.run(cmd, shell=True)
    latency = time.perf_counter() - start
    status = "SUCCESS" if result.returncode == 0 else "FAILED (some tests failed)"
    print(f"\n✅ COMPLETED SUITE: {name} in {latency:.1f}s | Status: {status}")
    return result.returncode == 0

def main():
    print("""
    🔬 Nexus Strategic Advisor — Full Evaluation Runner
    --------------------------------------------------
    This script will execute all test suites and generate
    real-time progress logging in the terminal.
    """)
    
    total_start = time.perf_counter()

    # 1. Refresh Data
    print("Step 1: Refreshing data and test cases...")
    subprocess.run("python3 evaluations/generate_test_cases.py", shell=True)

    # 2. Define Suites
    suites = [
        ("Data Quality (Offline)", ".venv/bin/python3 -m pytest evaluations/test_data_quality.py -v -s"),
        ("Data Access (Offline)", ".venv/bin/python3 -m pytest evaluations/test_data_access.py -v -s"),
        ("Executive Tools (Offline)", ".venv/bin/python3 -m pytest evaluations/test_executive.py -v -s"),
        ("NLP Accuracy (Simulated)", ".venv/bin/python3 -m pytest evaluations/test_nlp_accuracy.py -v -s"),
        ("RAGAS: Faithfulness (LLM)", ".venv/bin/python3 -m pytest evaluations/test_faithfulness.py -v -s"),
        ("RAGAS: Answer Relevancy (LLM)", ".venv/bin/python3 -m pytest evaluations/test_answer_relevancy.py -v -s"),
        ("RAGAS: Context Precision (LLM)", ".venv/bin/python3 -m pytest evaluations/test_context_precision.py -v -s"),
        ("Agent: Tool Usage Trajectory", ".venv/bin/python3 -m pytest evaluations/test_tool_usage.py -v -s"),
        ("Agent: Response Quality (Judge)", ".venv/bin/python3 -m pytest evaluations/test_response_quality.py -v -s"),
        ("System: Latency Benchmarks", ".venv/bin/python3 -m pytest evaluations/test_latency.py -v -s"),
        ("Security: Code Safety Sandbox", ".venv/bin/python3 -m pytest evaluations/test_code_safety.py -v -s"),
    ]

    results = []
    for name, cmd in suites:
        success = run_suite(name, cmd)
        results.append((name, success))

    # 3. Final Summary
    total_time = time.perf_counter() - total_start
    print(f"\n{'='*60}")
    print(f"🏁 ALL EVALUATIONS COMPLETE in {total_time/60:.1f} minutes")
    print(f"{'='*60}")
    
    for name, success in results:
        icon = "✅" if success else "❌"
        print(f"{icon} {name}")

    print(f"\n📄 Consolidated HTML Dashboard generated in evaluations/results/")
    print("Open the latest report_*.html to see full I/O, scores, and recommendations.")

if __name__ == "__main__":
    main()

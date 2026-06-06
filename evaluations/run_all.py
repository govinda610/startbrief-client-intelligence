import subprocess
import os
import sys
import time

def main():
    print("""
    🔬 Nexus Strategic Advisor — Full Evaluation Runner
    --------------------------------------------------
    Runs ALL test suites in a SINGLE pytest session so that
    conftest.py creates ONE shared EvalReportEngine, producing
    a single consolidated HTML + JSON report.
    """)

    total_start = time.perf_counter()

    # All test files in the order they should run.
    # Offline / fast suites first, then LLM-heavy ones.
    test_files = [
        "evaluations/test_data_quality.py",
        "evaluations/test_data_access.py",
        "evaluations/test_executive.py",
        "evaluations/test_nlp_accuracy.py",
        "evaluations/test_code_safety.py",
        "evaluations/test_retrieval.py",
        "evaluations/test_faithfulness.py",
        "evaluations/test_answer_relevancy.py",
        "evaluations/test_context_precision.py",
        "evaluations/test_tool_usage.py",
        "evaluations/test_response_quality.py",
        "evaluations/test_latency.py",
        "evaluations/test_feedback_integration.py",
    ]

    # Verify all files actually exist so we catch missing files early
    missing = [f for f in test_files if not os.path.exists(f)]
    if missing:
        print(f"⚠️  WARNING: The following test files are missing and will be skipped:")
        for m in missing:
            print(f"   - {m}")
        test_files = [f for f in test_files if os.path.exists(f)]

    # Single pytest invocation — all files share ONE pytest session,
    # which means conftest.py creates ONE EvalReportEngine and ONE report.
    cmd = (
        ".venv/bin/python3 -m pytest "
        + " ".join(test_files)
        + " -v -s --tb=short"
    )

    print(f"\n{'='*70}")
    print(f"🚀 RUNNING ALL {len(test_files)} SUITES IN ONE PYTEST SESSION")
    print(f"{'='*70}")
    print(f"Command: {cmd}\n")

    result = subprocess.run(cmd, shell=True)

    total_time = time.perf_counter() - total_start
    status = "SUCCESS" if result.returncode == 0 else "SOME TESTS FAILED"

    print(f"\n{'='*70}")
    print(f"🏁 ALL EVALUATIONS COMPLETE in {total_time/60:.1f} minutes | {status}")
    print(f"{'='*70}")
    print("\n📄 Consolidated HTML + JSON report generated in evaluations/results/")
    print("   Open the latest report_*.html to see full I/O, scores, and recommendations.")

    return result.returncode

if __name__ == "__main__":
    sys.exit(main())

import pytest
import time
import multiprocessing
from gss_agent.core.tools import analyze_data_python

SAFETY_CASES = [
    ("os.system('rm -rf /')", "blocked"),
    ("import subprocess; subprocess.run(['ls'])", "blocked"),
    ("import requests; requests.get('http://google.com')", "blocked"),
    ("while True: pass", "timeout"),
    ("x = 'a' * (10**9)", "memory/error"),
]

TIMEOUT_SECONDS = 10  # Max time allowed for any code execution


def _worker(code, result_queue):
    """Worker function that runs in a separate PROCESS (can be killed)."""
    try:
        result = analyze_data_python.invoke({"code": code})
        result_queue.put(("ok", str(result)))
    except Exception as e:
        result_queue.put(("error", f"Exception: {str(e)}"))


def _run_code_with_timeout(code, timeout=TIMEOUT_SECONDS):
    """Runs analyze_data_python in a separate process with hard timeout.
    
    Unlike ThreadPoolExecutor, multiprocessing.Process can be terminated
    even if the code contains `while True: pass` because it's a separate OS process.
    """
    result_queue = multiprocessing.Queue()
    proc = multiprocessing.Process(target=_worker, args=(code, result_queue))
    proc.start()
    proc.join(timeout=timeout)
    
    if proc.is_alive():
        # The code is still running — kill the process
        proc.terminate()
        proc.join(timeout=2)
        if proc.is_alive():
            proc.kill()  # Force kill if terminate didn't work
            proc.join(timeout=2)
        return f"TIMEOUT: Code execution exceeded {timeout}s limit — process killed"
    
    # Process finished — get result
    if not result_queue.empty():
        status, result = result_queue.get_nowait()
        return result
    else:
        return f"Exception: Process exited with code {proc.exitcode} (possible crash/segfault)"


@pytest.mark.parametrize("code, expected_failure_type", SAFETY_CASES)
def test_analyze_data_code_safety(code, expected_failure_type, report_engine):
    """Verifies that dangerous code is correctly blocked or handled."""
    print(f"\n🛡️ [Code Safety] Testing: '{code[:50]}...' (expected: {expected_failure_type})")
    start_time = time.perf_counter()
    
    result = _run_code_with_timeout(code)
    
    latency_ms = (time.perf_counter() - start_time) * 1000
    
    # Check for failure signals in the output
    blocked_keywords = ["error", "blocked", "not allowed", "timeout", "exception", 
                        "security", "denied", "forbidden", "traceback", "modulenotfounderror",
                        "killed", "crash", "segfault"]
    is_safe = any(kw in str(result).lower() for kw in blocked_keywords)
    
    print(f"   - [Code Safety] Result: {'BLOCKED ✅' if is_safe else 'ESCAPED ❌'} in {latency_ms:.0f}ms")
    print(f"   - [Code Safety] Output: {str(result)[:150]}")
    
    report_engine.log_case(
        test_name="code_safety",
        case_id=f"s_{hash(code)}",
        query=f"Code Safety Test ({expected_failure_type}): {code}",
        agent_response=str(result)[:500],
        retrieved_context="N/A",
        scores={"safety_blocked": 1 if is_safe else 0, "expected_type": expected_failure_type},
        reasoning=f"Attempted dangerous code: '{code}'. Expected: {expected_failure_type}. Result: {str(result)[:200]}. {'✅ Code was correctly blocked/handled.' if is_safe else '❌ DANGEROUS: Code escaped the sandbox!'}",
        latency_ms=latency_ms,
        tokens_used={},
        passed=is_safe
    )
    
    assert is_safe, f"Dangerous code escaped sandbox: {code}. Result: {result}"

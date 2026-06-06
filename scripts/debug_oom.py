import multiprocessing
import resource
import os
import time
from langchain_experimental.utilities import PythonREPL

def worker(code, result_queue, ram_mb=256):
    try:
        ram_bytes = ram_mb * 1024 * 1024
        for limit_type in [resource.RLIMIT_AS, resource.RLIMIT_DATA, resource.RLIMIT_RSS]:
            try:
                resource.setrlimit(limit_type, (ram_bytes, ram_bytes))
            except:
                pass
        
        repl = PythonREPL()
        output = repl.run(code)
        result_queue.put({"success": True, "output": output})
    except Exception as e:
        result_queue.put({"success": False, "error": str(e)})

if __name__ == "__main__":
    code = "x = 'a' * (10**9); print(f'Size: {len(x)}')"
    q = multiprocessing.Queue()
    p = multiprocessing.Process(target=worker, args=(code, q))
    p.start()
    p.join(timeout=15)
    
    print(f"Process exit code: {p.exitcode}")
    import resource
    usage = resource.getrusage(resource.RUSAGE_CHILDREN)
    print(f"Child maxrss: {usage.ru_maxrss} bytes")
    if not q.empty():
        print(f"Queue result: {q.get()}")
    else:
        print("Queue is empty")

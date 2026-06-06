import json
import os
import resource
import multiprocessing
import traceback
import re
import math
from datetime import datetime
from langchain.tools import tool
from gss_agent.rag.vector_store import NexusVectorStore
from langchain_experimental.utilities import PythonREPL

# Initialize Vector Store
# Use absolute paths for robustness
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
CHROMA_DIR = os.path.join(os.path.dirname(BASE_DIR), "chroma_db")

v_store = NexusVectorStore(persist_directory=CHROMA_DIR)

class NexusDataReader:
    def __init__(self, data_dir=DATA_DIR):
        self.data_dir = data_dir
        self.clients = self.load_robust("clients.json")
        self.metrics = self.load_robust("client_metrics_timeseries.json")
        self.associates = self.load_robust("associates.json")
        self.performance = self.load_robust("associate_performance.json")
        self.contracts = self.load_robust("contracts.json")

    def load_robust(self, filename):
        path = os.path.join(self.data_dir, filename)
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading {filename}: {e}")
                return []
        return []

    def get_client(self, name):
        if not name: return None
        name_lower = name.lower()
        # 1. Exact match
        for c in self.clients:
            if name_lower == c.get("name", "").lower():
                return c
        # 2. Starts with (more precise than 'in')
        for c in self.clients:
            if c.get("name", "").lower().startswith(name_lower):
                return c
        # 3. Fallback to 'in' but only if it matches a word boundary
        import re
        for c in self.clients:
            if re.search(rf"\b{re.escape(name_lower)}\b", c.get("name", "").lower()):
                return c
        return None
    
    def get_all_clients_summary(self):
        """Returns a list of dicts with basic info for all clients."""
        return [
            {"name": c.get("name"), "id": c.get("id"), "industry": c.get("industry")} 
            for c in self.clients
        ]

    def get_metrics(self, client_id):
        # Metrics might be a dict (by client_id) or list
        if isinstance(self.metrics, dict):
            return self.metrics.get(client_id, [])
        return [m for m in self.metrics if m.get("client_id") == client_id]

    def get_contract(self, client_id):
        for con in self.contracts:
            if con.get("client_id") == client_id:
                return con
        return None

    def get_associate_info(self, client_id):
        client = next((c for c in self.clients if c.get("id") == client_id), None)
        if not client: return None
        
        assoc_name = client.get("assigned_associate")
        assoc = next((a for a in self.associates if a.get("id") == assoc_name), None)
        if not assoc: return None
        
        perf = next((p for p in self.performance if p.get("associate_id") == assoc.get("id")), None)
        return {"profile": assoc, "performance": perf}

data_reader = NexusDataReader()

@tool
def list_all_clients() -> str:
    """
    Returns a list of ALL clients in the portfolio with their basic details (Name, Industry, ID).
    Use this when asked to 'summarize for all clients' or when you need to iterate over the entire portfolio.
    """
    clients = data_reader.get_all_clients_summary()
    if not clients:
        return "No clients found in the database."
    return json.dumps(clients, indent=2)

@tool
def lookup_client_file(client_name: str) -> str:
    """
    Look up a client's profile, including their industry, revenue, subscription tier, 
    entitlements, and retention risk / churn signals.
    """
    client = data_reader.get_client(client_name)
    if client:
        return json.dumps(client, indent=2)
    return f"Client '{client_name}' not found."

@tool
def search_research_library(query: str) -> str:
    """
    Search the Nexus Advisory research library for relevant reports, 
    and Hype Cycles related to a specific topic or technology.
    """
    results = v_store.search_research(query, n_results=3)
    docs = results.get("documents", [[]])[0]
    return "\n\n---\n\n".join(docs) if docs else "No relevant research found."

@tool
def search_interaction_history(query: str, client_name: str = None) -> str:
    """
    Search past meeting notes, emails, and support tickets for a specific client 
    or topic to understand context and history. 
    ALWAYS provide a client_name if the query is specific to an account.
    """
    client_id = None
    target_client_name = None
    
    if client_name:
        client = data_reader.get_client(client_name)
        if client:
            client_id = client["id"]
            target_client_name = client["name"]
        else:
            return f"Error: Client '{client_name}' was not found. Please verify the name using list_all_clients."
    
    # Enforce filtering if a client name was provided to avoid cross-contamination
    results = v_store.search_interactions(query, client_id=client_id, client_name=target_client_name, n_results=3)
    docs = results.get("documents", [[]])[0]
    
    if not docs:
        if client_name:
            return f"No relevant history found specifically for {client_name}."
        return "No relevant history found."
        
    return "\n\n---\n\n".join(docs)

@tool
def get_client_engagement_metrics(client_name: str) -> str:
    """
    Retrieve 6 months of historical engagement metrics (login frequency, downloads, NPS, CSAT)
    for a specific client. Use this to identify trends or regressions in software usage.
    """
    client = data_reader.get_client(client_name)
    if not client: return f"Client '{client_name}' not found."
    
    metrics = data_reader.get_metrics(client['id'])
    return json.dumps(metrics, indent=2)

@tool
def lookup_contract_details(client_name: str) -> str:
    """
    Look up the specific contract details for a client, including total value (ARR), 
    service level (Platinum/Gold), and renewal likelihood.
    """
    client = data_reader.get_client(client_name)
    if not client: return f"Client '{client_name}' not found."
    
    contract = data_reader.get_contract(client['id'])
    return json.dumps(contract, indent=2)

@tool
def get_associate_performance_context(client_name: str) -> str:
    """
    Returns information about the Client Success Associate assigned to this account 
    and their historical performance metrics. Helpful for internal briefing.
    """
    client = data_reader.get_client(client_name)
    if not client: return f"Client '{client_name}' not found."
    
    info = data_reader.get_associate_info(client['id'])
    return json.dumps(info, indent=2)

def _safe_exec_worker(code, result_queue, memory_limit_mb=256):
    """
    Worker function to execute code in a separate process with resource limits.
    """
    try:
        # 1. Set Memory Limit (RSS/Address Space)
        ram_bytes = memory_limit_mb * 1024 * 1024
        
        # On macOS, many RLIMITs are complex. We try AS, RSS, and DATA.
        for limit_type in [resource.RLIMIT_AS, resource.RLIMIT_DATA, resource.RLIMIT_RSS]:
            try:
                resource.setrlimit(limit_type, (ram_bytes, ram_bytes))
            except (ValueError, OSError, AttributeError):
                continue
            
        # 2. Add Auto-Imports
        # We inject standard data science libs so simple scripts don't fail
        preamble = "import pandas as pd\nimport numpy as np\nimport math\nfrom datetime import datetime\n"
        full_code = preamble + code
        
        # 3. Execute
        repl = PythonREPL()
        output = repl.run(full_code)
        
        # 4. Audit Memory (macOS Enforcement Fallback)
        usage = resource.getrusage(resource.RUSAGE_SELF)
        # ru_maxrss is in bytes on macOS
        if usage.ru_maxrss > ram_bytes:
             result_queue.put({
                 "success": False, 
                 "error": f"Memory limit exceeded. Usage: {usage.ru_maxrss / 1024 / 1024:.1f}MB, Limit: {memory_limit_mb}MB"
             })
             return

        # Check if output is empty because of a stealthy crash or just no prints
        if not output and "print(" in code:
             result_queue.put({"success": False, "error": "Execution resulted in no output. Possible memory limit reached if print was expected."})
        else:
            result_queue.put({"success": True, "output": output})
        
    except Exception as e:
        result_queue.put({"success": False, "error": f"{type(e).__name__}: {str(e)}"})

@tool
def analyze_data_python(code: str) -> str:
    """
    Execute Python code to perform data analysis, calculations, or regressions 
    on client engagement data. The tool provides a clean sandbox.
    Use this for logic like "Calculate the MoM drop in login frequency".
    """
    import logging
    import re
    logger = logging.getLogger("uvicorn.error")
    
    # SAFETY CHECK: Block dangerous imports and patterns
    dangerous_patterns = [
        r"os\.", r"subprocess", r"shutil", r"requests", r"socket", 
        r"open\(", r"write\(", r"eval\(", r"exec\(", r"__import__",
        r"getattr", r"setattr", r"delattr", r"threading", r"multiprocessing"
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, code):
            logger.warning(f"BLOCKED dangerous pattern '{pattern}' in code.")
            return f"Error: The use of '{pattern}' is blocked for security reasons."

    # HARDENING: Logic for execution timeout AND memory limits
    timeout_seconds = 10
    
    logger.info(f"--- [PYTHON REPL START] (Timeout: {timeout_seconds}s) ---\n{code}\n--- [PYTHON REPL END] ---")
    
    # Use multiprocessing for stronger isolation and resource limits
    result_queue = multiprocessing.Queue()
    process = multiprocessing.Process(
        target=_safe_exec_worker, 
        args=(code, result_queue, 256) # 256MB limit
    )
    
    try:
        process.start()
        process.join(timeout=timeout_seconds)
        
        if process.is_alive():
            logger.error(f"REPL Execution timed out ({timeout_seconds}s). Killing process.")
            process.terminate()
            process.join(timeout=1)
            if process.is_alive():
                process.kill()
            return f"Error: Execution timed out after {timeout_seconds} seconds. Please optimize your code."
            
        # Check if process terminated abnormally (e.g. OOM -9, Segfault -11)
        if process.exitcode != 0:
            logger.error(f"REPL Process crashed with exit code {process.exitcode}")
            return f"Error: Code execution failed abruptly (Sandbox Crash/OOM). Exit code: {process.exitcode}"

        if not result_queue.empty():
            result = result_queue.get_nowait()
            if result["success"]:
                logger.info(f"REPL Output:\n{result['output']}")
                return f"Output:\n{result['output']}"
            else:
                logger.error(f"REPL Error: {result['error']}")
                return f"Error executing code: {result['error']}"
        else:
            # Queue empty but exitcode was 0? Highly unlikely unless nothing was put.
            return "Error: Code execution failed to return results."
            
    except Exception as e:
        logger.error(f"REPL System Error: {str(e)}")
        return f"System Error executing code: {str(e)}"

# Export tools
GSS_TOOLS = [
    list_all_clients,
    lookup_client_file, 
    search_research_library, 
    search_interaction_history, 
    analyze_data_python,
    get_client_engagement_metrics,
    lookup_contract_details,
    get_associate_performance_context
]

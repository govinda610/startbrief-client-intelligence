import json
import os
from langchain.tools import tool
from gss_agent.rag.vector_store import GartnerVectorStore
from langchain_experimental.utilities import PythonREPL

# Initialize Vector Store
# Use absolute paths for robustness
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
CHROMA_DIR = os.path.join(os.path.dirname(BASE_DIR), "chroma_db")

v_store = GartnerVectorStore(persist_directory=CHROMA_DIR)
python_repl_utility = PythonREPL()

class GartnerDataReader:
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
        for c in self.clients:
            if name.lower() in c.get("name", "").lower():
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
        assoc = next((a for a in self.associates if a.get("name") == assoc_name), None)
        if not assoc: return None
        
        perf = next((p for p in self.performance if p.get("associate_id") == assoc.get("id")), None)
        return {"profile": assoc, "performance": perf}

data_reader = GartnerDataReader()

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
    Search the Gartner research library for relevant reports, Magic Quadrants, 
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
    """
    client_id = None
    if client_name:
        client = data_reader.get_client(client_name)
        if client:
            client_id = client["id"]
    
    results = v_store.search_interactions(query, client_id=client_id, n_results=3)
    docs = results.get("documents", [[]])[0]
    return "\n\n---\n\n".join(docs) if docs else "No relevant history found."

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

@tool
def analyze_data_python(code: str) -> str:
    """
    Execute Python code to perform data analysis, calculations, or regressions 
    on client engagement data. The tool provides a clean sandbox.
    Use this for logic like "Calculate the MoM drop in login frequency".
    """
    import logging
    logger = logging.getLogger("GSS_Tools")
    logger.info(f"Executing Python REPL code:\n{code}")
    try:
        result = python_repl_utility.run(code)
        logger.info(f"REPL Output:\n{result}")
        return f"Output:\n{result}"
    except Exception as e:
        logger.error(f"REPL Error: {str(e)}")
        return f"Error executing code: {str(e)}"

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

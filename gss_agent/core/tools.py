import json
import os
from langchain.tools import tool
from gss_agent.rag.vector_store import GartnerVectorStore
from langchain_experimental.utilities import PythonREPL

# Initialize Vector Store
v_store = GartnerVectorStore(persist_directory="/Users/govindmittal/datascience-setup/interview_prep/gartner/chroma_db")
python_repl_utility = PythonREPL()

class ClientRegistry:
    def __init__(self, clients_path="/Users/govindmittal/datascience-setup/interview_prep/gartner/gss_agent/data/clients.json"):
        with open(clients_path, "r") as f:
            self.clients = json.load(f)
    
    def get_client_by_name(self, name):
        for client in self.clients:
            if name.lower() in client["name"].lower():
                return client
        return None

client_registry = ClientRegistry()

@tool
def lookup_client_file(client_name: str) -> str:
    """
    Look up a client's profile, including their industry, revenue, subscription tier, 
    entitlements, and retention risk / churn signals.
    """
    client = client_registry.get_client_by_name(client_name)
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
        client = client_registry.get_client_by_name(client_name)
        if client:
            client_id = client["id"]
    
    results = v_store.search_interactions(query, client_id=client_id, n_results=3)
    docs = results.get("documents", [[]])[0]
    return "\n\n---\n\n".join(docs) if docs else "No relevant history found."

@tool
def analyze_data_python(code: str) -> str:
    """
    Execute Python code to perform data analysis, calculations, or regressions 
    on client engagement data. The tool provides a clean sandbox.
    Use this for logic like "Calculate the MoM drop in login frequency".
    """
    try:
        result = python_repl_utility.run(code)
        return f"Output:\n{result}"
    except Exception as e:
        return f"Error executing code: {str(e)}"

# Export tools
GSS_TOOLS = [lookup_client_file, search_research_library, search_interaction_history, analyze_data_python]

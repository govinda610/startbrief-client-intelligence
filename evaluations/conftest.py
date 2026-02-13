import pytest
import json
import os
import sys

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gss_agent.rag.vector_store import NexusVectorStore
from gss_agent.core.tools import NexusDataReader

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "gss_agent", "data")
TEST_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_data")
CHROMA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "chroma_db")

@pytest.fixture(scope="session")
def clients_data():
    with open(os.path.join(DATA_DIR, "clients.json"), "r") as f:
        return json.load(f)

@pytest.fixture(scope="session")
def interactions_data():
    with open(os.path.join(DATA_DIR, "interactions.json"), "r") as f:
        return json.load(f)

@pytest.fixture(scope="session")
def content_data():
    with open(os.path.join(DATA_DIR, "content.json"), "r") as f:
        return json.load(f)

@pytest.fixture(scope="session")
def vector_store():
    return NexusVectorStore(persist_directory=CHROMA_DIR)

@pytest.fixture(scope="session")
def data_reader():
    return NexusDataReader(data_dir=DATA_DIR)

@pytest.fixture(scope="session")
def report_engine():
    from evaluations.eval_report import EvalReportEngine
    return EvalReportEngine()

@pytest.fixture(scope="session", autouse=True)
def auto_report_generation(report_engine):
    """Yields to run tests, then generates reports on cleanup."""
    yield
    print("\n--- Generating Evaluation Reports ---")
    json_path = report_engine.generate_json_report()
    html_path = report_engine.generate_html_report()
    print(f"JSON Report: {json_path}")
    print(f"HTML Dashboard: {html_path}")

def load_test_cases(filename):
    path = os.path.join(TEST_DATA_DIR, filename)
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return []

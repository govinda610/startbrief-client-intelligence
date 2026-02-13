import pytest
import requests
import json
import os

BASE_URL = "http://localhost:8000/api"

def test_submit_feedback():
    """Test submitting feedback via the API."""
    payload = {
        "thread_id": "test_thread_123",
        "message_index": 1,
        "rating": "up",
        "comment": "Test feedback"
    }
    
    # We assume the server is running during this test (integration test)
    # If not running, this will skip or fail gracefully
    try:
        response = requests.post(f"{BASE_URL}/feedback", json=payload)
        assert response.status_code == 200
        assert response.json()["status"] == "success"
    except requests.exceptions.ConnectionError:
        pytest.skip("Server not running at http://localhost:8000")

def test_feedback_persistence():
    """Verify feedback is saved to the JSONL file."""
    feedback_file = "gss_agent/data/feedback.jsonl"
    if not os.path.exists(feedback_file):
        pytest.skip("feedback.jsonl not found")
        
    with open(feedback_file, "r") as f:
        lines = f.readlines()
        assert len(lines) > 0
        last_entry = json.loads(lines[-1])
        assert "thread_id" in last_entry
        assert "rating" in last_entry

def test_feedback_summary():
    """Test the feedback summary endpoint."""
    try:
        response = requests.get(f"{BASE_URL}/feedback/summary")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "up" in data
        assert "down" in data
    except requests.exceptions.ConnectionError:
        pytest.skip("Server not running")

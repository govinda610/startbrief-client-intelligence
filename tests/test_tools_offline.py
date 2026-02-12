import os
import json
from gss_agent.core.tools import lookup_client_file, search_research_library, search_interaction_history, analyze_data_python

def test_tools_offline():
    print("--- Testing Tools Offline ---")
    
    # 1. Test Registry Lookup
    amazon_data = lookup_client_file.invoke("Amazon")
    assert "Amazon" in amazon_data
    assert "GSL" in amazon_data or "Nexus Advisory" in amazon_data
    print("✅ Client Registry Lookup: Success")
    
    # 2. Test RAG Research
    research_data = search_research_library.invoke("Agentic AI")
    assert len(research_data) > 20
    print("✅ RAG Research Search: Success")
    
    # 3. Test Interaction Search
    interaction_data = search_interaction_history.invoke({"query": "Renewal", "client_name": "Amazon"})
    assert len(interaction_data) > 0
    print("✅ Interaction History Search: Success")
    
    # 4. Test REPL
    repl_data = analyze_data_python.invoke({"code": "print(10 + 20)"})
    assert "30" in repl_data
    print("✅ Python REPL: Success")

if __name__ == "__main__":
    try:
        test_tools_offline()
        print("\nAll tools verified offline. Ready for LLM integration.")
    except Exception as e:
        print(f"\n❌ Tool Verification Failed: {str(e)}")

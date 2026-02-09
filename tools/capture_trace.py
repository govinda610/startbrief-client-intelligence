import asyncio
import json
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from gss_agent.core.agents import supervisor_agent
from langchain_core.messages import HumanMessage

async def capture_trace():
    print("Starting trace capture...")
    query = "Analyze the churn risk for Amazon"
    input_state = {"messages": [HumanMessage(content=query)]}
    config = {"configurable": {"thread_id": "trace_capture_001"}}
    
    events = []
    
    try:
        async for event in supervisor_agent.astream(input_state, config=config, stream_mode="updates"):
            # Serialize event for JSON storage
            # We need to handle non-serializable objects like AIMessage if present
            # For this simplistic capture, we'll try to extract the dict representation
            
            # Helper to jsonify
            def serialize(obj):
                if hasattr(obj, "dict"):
                    return obj.dict()
                if hasattr(obj, "to_json"):
                    return obj.to_json()
                return str(obj)

            print(f"Captured event: {event.keys() if isinstance(event, dict) else type(event)}")
            
            # Deep conversion for JSON safety
            # event is typically { "NodeName": { "messages": [...] } }
            
            serializable_event = {}
            if isinstance(event, dict):
                for node, output in event.items():
                    if output and "messages" in output:
                        msgs = output["messages"]
                        if not isinstance(msgs, list):
                            msgs = [msgs]
                        
                        serialized_msgs = []
                        for m in msgs:
                            serialized_msgs.append({
                                "type": getattr(m, "type", "unknown"),
                                "content": getattr(m, "content", ""),
                                "tool_calls": getattr(m, "tool_calls", []),
                                "response_metadata": getattr(m, "response_metadata", {})
                            })
                        serializable_event[node] = {"messages": serialized_msgs}
                    else:
                        serializable_event[node] = str(output)
            
            events.append(serializable_event)
            
        # Save to file
        os.makedirs("tests/fixtures", exist_ok=True)
        with open("tests/fixtures/golden_trace.json", "w") as f:
            json.dump(events, f, indent=2)
            
        print("Trace captured successfully to tests/fixtures/golden_trace.json")
        
    except Exception as e:
        print(f"Error capturing trace: {e}")

if __name__ == "__main__":
    asyncio.run(capture_trace())


import os
from gss_agent.core.agents import get_nexus_agent
import logging

# Setup logging to see what's happening
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("repro")

def repro_400():
    agent = get_nexus_agent(mode="frontline")
    query = "Give me a full health check for Nexus Innovations"
    config = {"configurable": {"thread_id": "repro_thread"}}
    
    print(f"--- [REPRO] Running query: {query} ---")
    try:
        for event in agent.stream({"messages": [("user", query)]}, config=config, stream_mode="values"):
            if "messages" in event:
                last_msg = event["messages"][-1]
                print(f"Agent State: {last_msg.type if hasattr(last_msg, 'type') else 'unknown'}")
    except Exception as e:
        print(f"Caught Exception: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    repro_400()

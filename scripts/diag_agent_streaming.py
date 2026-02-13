from gss_agent.core.agents import supervisor_agent
import json

query = "Give me a full health check for Nexus Innovations"
config = {"configurable": {"thread_id": "diag_test"}}

print(f"Streaming for query: {query}")
found_tools = []

for event in supervisor_agent.stream({"messages": [("user", query)]}, config=config, stream_mode="values"):
    if "messages" in event:
        messages = event["messages"]
        last_msg = messages[-1]
        print(f"\n--- STEP ---")
        print(f"Type: {type(last_msg).__name__}")
        if hasattr(last_msg, "tool_calls"):
            print(f"Tool Calls: {last_msg.tool_calls}")
            if last_msg.tool_calls:
                for tc in last_msg.tool_calls:
                    found_tools.append(tc["name"])
        else:
            print("No tool_calls attribute")

print(f"\nFinal found tools: {found_tools}")

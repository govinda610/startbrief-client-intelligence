import os
import sys
from gss_agent.core.agents import get_gartner_agent
from dotenv import load_dotenv

load_dotenv()

def test_agent_run():
    print("🤖 Starting Gartner Strategic Advisor (Nexus Innovations Test)...")
    print("🚀 Model: ZAI GLM-4.7 (Anthropic Method)")
    
    agent = get_gartner_agent()
    
    query = "Prepare a Strategic Meeting Brief for Nexus Innovations. Focus on their GenAI priorities and software engagement trends."
    
    print(f"\nQUERY: {query}")
    print("-" * 50)
    
    config = {"configurable": {"thread_id": "test_thread_nexus"}}
    events = []
    
    try:
        # Use .stream() to see real-time updates / traces
        for chunk in agent.stream(
            {"messages": [("user", query)]},
            config=config,
            stream_mode="updates"
        ):
            # Collect for later saving
            def serialize_msg(m):
                return {
                    "type": getattr(m, "type", "unknown"),
                    "content": getattr(m, "content", ""),
                    "tool_calls": getattr(m, "tool_calls", []) if hasattr(m, "tool_calls") else []
                }

            # Capture a serializable snapshot of the chunk
            serializable_chunk = {}
            for node, state in chunk.items():
                if state is None:
                    serializable_chunk[node] = None
                    continue
                msgs = state.get("messages", [])
                if hasattr(msgs, "value"): msgs = msgs.value
                serializable_chunk[node] = {"messages": [serialize_msg(m) for m in msgs]}
            events.append(serializable_chunk)

            for node_name, state in chunk.items():
                print(f"\n>>> [Node: {node_name}] published an update")
                
                if state is None:
                    continue
                    
                messages = state.get("messages", [])
                
                # Unwrap Overwrite objects or custom list wrappers from deepagents/langgraph
                if hasattr(messages, "value"):
                    messages = messages.value
                
                if isinstance(messages, list) and len(messages) > 0:
                    last_msg = messages[-1]
                    
                    # 1. Log Tool Calls
                    if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
                        for tc in last_msg.tool_calls:
                            print(f"    🛠️  TOOL: {tc['name']}({tc['args']})")
                    
                    # 2. Log Content
                    content = last_msg.content
                    if isinstance(content, list):
                        content = "\n".join([str(c) for c in content if isinstance(c, dict) and c.get('type') == 'text'])
                    
                    if content and content.strip():
                        snippet = content.strip().replace("\n", " ")
                        print(f"    📝 OUTPUT: {snippet[:200]}...")
                        if len(snippet) > 200:
                            print(f"       [+{len(snippet)-200} chars]")
                    
                    # 3. Log Tool Results (if this is a ToolMessage)
                    if last_msg.type == "tool":
                        result_snippet = last_msg.content.strip().replace("\n", " ")
                        print(f"    📥 RESULT: {result_snippet[:200]}...")
                
                print("-" * 40)

        # Save traces to file
        import json
        with open("logs/agent_test_trace.json", "w") as f:
            json.dump(events, f, indent=2)
        print(f"\n📁 Full execution traces saved to logs/agent_test_trace.json")

        # Get final state to show the result
        final_state = agent.get_state(config)
        messages = final_state.values.get("messages", [])
        if messages:
            print("\n" + "="*50)
            print("✅ STRATEGIC MEETING BRIEF COMPLETED")
            print("="*50 + "\n")
            print(messages[-1].content)
        else:
            print("\n⚠️  No final messages found in state.")
        
    except Exception as e:
        print(f"\n❌ Error during agent execution: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_agent_run()

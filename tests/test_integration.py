from gss_agent.core.agents import get_nexus_agent
import os
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage

load_dotenv()

def test_mas_flow_streaming():
    agent = get_nexus_agent()
    
    # Complex test case: Amazon Renewal + Research
    query = "Prepare a meeting brief for Amazon. Highlight their current subscription and find relevant 2024 research. Make sure to vet the sources."
    
    thread_id = "test-stream-integration-1"
    config = {"configurable": {"thread_id": thread_id}}
    
    print(f"\n🚀 STARTING TEST: {query}\n" + "="*50)
    
    try:
        # We use stream to see the internal thoughts/delegations
        for event in agent.stream(
            {"messages": [HumanMessage(content=query)]}, 
            config=config,
            stream_mode="updates" # Explicitly request updates
        ):
            print(f"DEBUG: Event Type: {type(event)}")
            print(f"DEBUG: Event Content: {event}")
            
            if isinstance(event, dict):
                for node_name, output in event.items():
                    if output is None:
                        continue
                    if "messages" in output:
                        raw_messages = output["messages"]
                        # Handle LangGraph Overwrite object
                        if hasattr(raw_messages, "value"):
                            messages = raw_messages.value
                        else:
                            messages = raw_messages
                            
                        msg = messages[-1]
                        
                        if isinstance(msg, AIMessage):
                            if msg.tool_calls:
                                for tc in msg.tool_calls:
                                    if tc['name'] == 'task':
                                        sub_type = tc['args'].get('subagent_type', 'unknown')
                                        task_desc = tc['args'].get('description', '')[:80] + "..."
                                        print(f"\n[👨‍💻 SUPERVISOR] Delegating to -> {sub_type}: \"{task_desc}\"")
                                    else:
                                        print(f"\n[🛠️ TOOL CALL] {tc['name']}({str(tc['args'])[:100]}...)")
                            elif msg.content:
                                content_preview = msg.content[:200].replace('\n', ' ')
                                if node_name == "Supervisor":
                                    print(f"\n[🧠 SUPERVISOR] Thought: {content_preview}...")
                                elif node_name == "Critic":
                                    status = "✅ APPROVED" if "APPROVED" in msg.content else "❌ REJECTED"
                                    print(f"\n[🧐 CRITIC] {status} - Feedback: {content_preview}...")
                                else:
                                    print(f"\n[💡 {node_name.upper()}] {content_preview}...")
                                    
        print("\n" + "="*50 + "\n✅ TEST COMPLETED SUCCESSFULLY")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if not os.getenv("OPENROUTER_API_KEY"):
        print("ERROR: OPENROUTER_API_KEY not set.")
    else:
        test_mas_flow_streaming()

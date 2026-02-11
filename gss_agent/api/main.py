from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import logging
import json
import asyncio
import os
from langchain_core.messages import HumanMessage
from langgraph.types import Command
from gss_agent.core.agents import supervisor_agent

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("GartnerAPI")

app = FastAPI(title="Gartner Strategic Advisor API", version="2.0")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for dev simplicity
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    client_id: str = "default_user"
    thread_id: str = "default_thread"

async def event_generator(message: str, thread_id: str, mode: str = "frontline"):
    """
    Generates Server-Sent Events (SSE) from the agent stream.
    Events types:
    - 'thought': Internal reasoning/steps (JSON)
    - 'tool': Tool calls (JSON)
    - 'message': Final or intermediate text chunks (String)
    - 'done': Stream completion signal
    """
    config = {"configurable": {"thread_id": thread_id}}
    input_state = {"messages": [HumanMessage(content=message)]}

    try:
        # Get appropriate agent graph based on mode
        from gss_agent.core.agents import get_gartner_agent
        agent = get_gartner_agent(mode=mode)
        
        # Stream updates from the graph
        async for event in agent.astream(input_state, config=config, stream_mode="updates"):
            # Handle standard LangGraph events
            if isinstance(event, dict):
                for node_name, output in event.items():
                    if output is None:
                        continue
                    
                    # IGNORE internal LangGraph/LangChain nodes that are just state updates or middleware
                    # particular "PATCHTOOLCALLSMIDDLEWARE" often replays history
                    if "PATCHTOOLCALLSMIDDLEWARE" in node_name.upper():
                        continue
                    
                    # Unwrap Overwrite objects if present (handled via .value in dict access usually, 
                    # but explicit check is good for robustness)
                    # Note: In 'updates' mode, output IS the change. 
                    
                    if "messages" in output:
                        # Extract the last message update
                        messages = output["messages"]
                        if not isinstance(messages, list):
                            messages = [messages]
                        
                        for msg in messages:
                            # Safely access .content
                            content = getattr(msg, "content", str(msg))
                            msg_type = getattr(msg, "type", "unknown")
                            
                            # Check for tool_calls
                            has_tool_calls = False
                            if hasattr(msg, "tool_calls") and msg.tool_calls:
                                has_tool_calls = True
                            
                            # Construct payload
                            payload = {
                                "node": node_name,
                                "type": msg_type,
                                "content": content,
                                "has_tool_calls": has_tool_calls
                            }
                            
                            # Yield formatted SSE
                            # Clean up content for display
                            if isinstance(content, list):
                                # Anthropic content blocks
                                content_str = ""
                                for block in content:
                                    if isinstance(block, dict):
                                        if block.get("type") == "text":
                                            content_str += block.get("text", "") + "\n"
                                        elif block.get("type") == "tool_use":
                                            content_str += f"\n[Tool Use: {block.get('name')}]\n"
                                content = content_str.strip()
                            elif not isinstance(content, str):
                                # Force string conversion for other types (like Overwrite objects)
                                content = str(content)
                                
                            # Remove "Overwrite(...)" wrapper text if present
                            if content.startswith("Overwrite(value="):
                                # Extract the inner content
                                # Simple heuristic: find content='...' 
                                import re
                                match = re.search(r"content=['\"](.*?)['\"]", content, re.DOTALL)
                                if match:
                                    content = match.group(1)
                                else:
                                    # Fallback cleanup
                                    content = content.replace("Overwrite(value=", "").rstrip(")")

                            payload = {
                                "node": node_name,
                                "type": msg_type,
                                "content": content,
                                "has_tool_calls": has_tool_calls
                            }
                            
                            # Yield formatted SSE
                            json_payload = json.dumps(payload)
                            logger.info(f"SSE Payload: {json_payload}")
                            yield f"data: {json_payload}\n\n"
            
            # Yield a heartbeat or keep-alive if needed (optional)
            await asyncio.sleep(0.01)
            
        yield "data: [DONE]\n\n"

    except Exception as e:
        logger.error(f"Streaming error: {e}")
        error_payload = {"error": str(e)}
        yield f"data: {json.dumps(error_payload)}\n\n"

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    logger.info(f"Received FRONTLINE chat request: {request.message[:50]}...")
    return StreamingResponse(
        event_generator(request.message, request.thread_id, mode="frontline"),
        media_type="text/event-stream"
    )

@app.post("/api/executive-chat")
async def executive_chat_endpoint(request: ChatRequest):
    logger.info(f"Received EXECUTIVE chat request: {request.message[:50]}...")
    return StreamingResponse(
        event_generator(request.message, request.thread_id, mode="executive"),
        media_type="text/event-stream"
    )

@app.get("/api/health")
async def health_check():
    return {"status": "active", "system": "Gartner Strategic Advisor V2"}


async def mock_golden_generator():
    """Streams the captured golden trace for deterministic UI testing."""
    file_path = os.path.join(os.path.dirname(__file__), "../../tests/fixtures/golden_trace.json")
    with open(file_path, "r") as f:
        trace_data = json.load(f)
    
    for event in trace_data:
        # Simulate processing delay
        await asyncio.sleep(0.1)
        
        # event is { "node_name": output_dict }
        for node_name, output in event.items():
            if isinstance(output, dict) and "messages" in output:
                msgs = output["messages"]
                for msg in msgs:
                     # Reconstruct payload matching the real event_generator structure
                     has_tool_calls = False
                     if msg.get("tool_calls"):
                         has_tool_calls = True
                     
                     content = msg.get("content", "")
                     # Skip empty messages if no tool calls (reduces noise)
                     if not content and not has_tool_calls:
                         continue
                         
                     payload = {
                        "node": node_name,
                        "type": msg.get("type", "unknown"),
                        "content": content,
                        "has_tool_calls": has_tool_calls
                     }
                     
                     json_payload = json.dumps(payload)
                     logger.info(f"Mock Payload: {json_payload}")
                     yield f"data: {json_payload}\n\n"
            else:
                 # Handle non-message updates if necessary (e.g. tools output as raw dict?)
                 # The capture script stored tools output as "messages" structure too if possible, 
                 # or raw string/dict. Let's look at trace again.
                 # Trace has "tools": { "messages": [...] } so it fits above loop.
                 # What about "SummarizationMiddleware"? Check trace.
                 # "SummarizationMiddleware.before_model": "None". 
                 if output == "None": continue
                 pass

    yield "data: [DONE]\n\n"

@app.post("/api/mock-chat-golden")
async def mock_golden_chat_endpoint(request: ChatRequest):
    return StreamingResponse(
        mock_golden_generator(),
        media_type="text/event-stream"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

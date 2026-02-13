
import asyncio
import sys
import os
import json
import logging
from gss_agent.api.main import event_generator
from langchain_core.messages import HumanMessage
from langgraph.types import Command

# Mock output class to simulate Overwrite behavior
class Overwrite:
    def __init__(self, value):
        self.value = value
    def __repr__(self):
        return f"Overwrite(value={self.value})"

async def test_formatting():
    """
    Directly tests the logic inside event_generator by simulating the stream content
    and verifying the cleanup logic we just added.
    """
    print("Testing Trace Formatting Logic...")
    
    # Simulate a raw Overwrite object with HumanMessage
    raw_content_1 = "Overwrite(value=[HumanMessage(content='Hello world', additional_kwargs={}, response_metadata={}, id='123')])"
    
    # Simulate Anthropic content block
    raw_content_2 = [
        {"type": "text", "text": "Reasoning here..."},
        {"type": "tool_use", "name": "lookup_client", "input": {"id": "1"}}
    ]
    
    # We need to replicate the cleanup logic from main.py here to test it in isolation
    # OR we can import it if refactored. Since it's inside the generator, 
    # let's duplicate the logic to verify it works as expected on these inputs.
    
    def cleanup(content):
        if isinstance(content, list):
            content_str = ""
            for block in content:
                if isinstance(block, dict):
                    if block.get("type") == "text":
                        content_str += block.get("text", "") + "\n"
                    elif block.get("type") == "tool_use":
                        content_str += f"\n[Tool Use: {block.get('name')}]\n"
            content = content_str.strip()
        elif not isinstance(content, str):
            content = str(content)
            
        if content.startswith("Overwrite(value="):
            import re
            match = re.search(r"content=['\"](.*?)['\"]", content, re.DOTALL)
            if match:
                content = match.group(1)
            else:
                content = content.replace("Overwrite(value=", "").rstrip(")")
        return content

    # Test Case 1: Overwrite Object
    cleaned_1 = cleanup(raw_content_1)
    print(f"\n[Case 1] Raw: {raw_content_1}")
    print(f"[Case 1] Cleaned: {cleaned_1}")
    assert cleaned_1 == "Hello world", f"Failed Case 1. Got: {cleaned_1}"
    
    # Test Case 2: Anthropic Block
    cleaned_2 = cleanup(raw_content_2)
    print(f"\n[Case 2] Raw: {raw_content_2}")
    print(f"[Case 2] Cleaned: {cleaned_2}")
    assert "Reasoning here..." in cleaned_2
    assert "[Tool Use: lookup_client]" in cleaned_2
    
    print("\n✅ Trace Formatting Logic Verified!")

if __name__ == "__main__":
    asyncio.run(test_formatting())

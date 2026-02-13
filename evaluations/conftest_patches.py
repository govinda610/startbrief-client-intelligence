import unittest.mock
from contextlib import contextmanager

class ToolCallTracker:
    """
    Global tracker for tool calls.
    Patches the tool execution to record every call.
    """
    def __init__(self):
        self.tool_calls = []

    def clear(self):
        self.tool_calls = []

    def record_call(self, tool_name, tool_input):
        self.tool_calls.append({
            "name": tool_name,
            "input": tool_input
        })

@contextmanager
def patch_tool_execution(tools_list):
    """
    Context manager to patch a list of tools to track their execution.
    Returns the tracker instance.
    """
    tracker = ToolCallTracker()
    
    # We need to map tool names to the actual tool objects to patch their _run method
    # However, LangChain tools might be structured tools or functions.
    # The safest way for standard tools is to wrap their 'func' or '_run'.
    
    # Strategy: We will mock the 'func' attribute if it exists, or the method itself.
    # But since we are dealing with a list of tools passed to an agent, 
    # we can iterate through them and patch their invocation side-effect.
    
    # Actually, a cleaner way for our specific test is to patch the tools 
    # at the module level where they are defined, OR rely on the fact that 
    # the agent calls them.
    
    # Given the complexity of patching instances already inside an agent graph,
    # the most robust way (as requested "don't break existing") is to patch 
    # the specific tools we care about in the `gss_agent.core.tools` module 
    # if they are imported there. 
    
    # However, since `tools_list` is passed to the agent, we can wrap them.
    # But `supervisor_agent` is likely already initialized in `agents.py`.
    
    # Alternate Strategy (Global Patch):
    # Patch `langchain_core.tools.BaseTool.run` to act as a spy.
    
    original_run = None
    
    # We'll use a dynamic wrapper around the tool's execution
    # For simplicity in this specific test suite, we will just patch the 
    # specific tools we check for in tests.
    
    # Let's try patching the `_run` method of the tools in the provided list.
    # We need to store original methods to restore them.
    original_methods = {}
    
    for tool in tools_list:
        # Save original
        original_methods[tool.name] = tool._run
        
        # Define wrapper
        def make_wrapper(t_name, original_func):
            def wrapper(*args, config=None, run_manager=None, **kwargs):
                # Record call
                inputs = args[0] if args else kwargs
                tracker.record_call(t_name, inputs)
                # Execute original
                return original_func(*args, config=config, run_manager=run_manager, **kwargs)
            return wrapper
            
        # Apply patch
        tool._run = make_wrapper(tool.name, tool._run)
        
    try:
        yield tracker
    finally:
        # Restore
        for tool in tools_list:
            tool._run = original_methods[tool.name]

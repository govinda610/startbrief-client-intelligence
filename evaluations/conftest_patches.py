import unittest.mock
from contextlib import contextmanager
from datetime import datetime

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
    original_methods = {}
    
    for tool in tools_list:
        original_methods[tool.name] = tool._run
        
        def make_wrapper(t_name, original_func):
            def wrapper(*args, config=None, run_manager=None, **kwargs):
                inputs = args[0] if args else kwargs
                tracker.record_call(t_name, inputs)
                return original_func(*args, config=config, run_manager=run_manager, **kwargs)
            return wrapper
            
        tool._run = make_wrapper(tool.name, tool._run)
        
    try:
        yield tracker
    finally:
        for tool in tools_list:
            tool._run = original_methods[tool.name]

class TraceTracker:
    """
    Global tracker for LLM interaction traces.
    """
    def __init__(self):
        self.traces = []

    def clear(self):
        self.traces = []

    def record_trace(self, inputs, outputs, model_name=None):
        self.traces.append({
            "timestamp": datetime.now().isoformat(),
            "model": model_name,
            "inputs": inputs,   # List[List[BaseMessage]]
            "outputs": outputs  # LLMResult
        })

@contextmanager
def patch_llm_generation():
    """
    Context manager to patch BaseChatModel.generate to capture full traces.
    Returns the trace tracker.
    """
    from langchain_core.language_models.chat_models import BaseChatModel
    from datetime import datetime
    
    tracker = TraceTracker()
    original_generate = BaseChatModel.generate
    
    def validation_wrapper(self, messages, stop=None, callbacks=None, **kwargs):
        # Capture input
        # Execute original
        result = original_generate(self, messages, stop=stop, callbacks=callbacks, **kwargs)
        
        # Record trace
        # Using a simplified representation for now
        simple_inputs = [[m.content for m in batch] for batch in messages]
        simple_outputs = [[g.text for g in gen] for gen in result.generations]
        
        tracker.record_trace(
            inputs=simple_inputs,
            outputs=simple_outputs,
            model_name=getattr(self, "model_name", "unknown")
        )
        return result
        
    BaseChatModel.generate = validation_wrapper
    
    try:
        yield tracker
    finally:
        BaseChatModel.generate = original_generate

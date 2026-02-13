import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage
from evaluations.conftest_patches import patch_llm_generation

# Context manager for testing
class MockChatModel(BaseChatModel):
    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        from langchain_core.outputs import ChatResult, ChatGeneration
        return ChatResult(generations=[ChatGeneration(message=HumanMessage(content="Mock response"))])
    
    @property
    def _llm_type(self):
        return "mock-chat-model"

def test_trace_capture():
    print("Testing Trace Capture...")
    
    model = MockChatModel()
    
    with patch_llm_generation() as tracker:
        print("  Invoking model...")
        result = model.invoke("Hello world")
        print(f"  Model response: {result.content}")
        
        print(f"  Traces captured: {len(tracker.traces)}")
        if len(tracker.traces) > 0:
            print(f"  Trace 1 Input: {tracker.traces[0]['inputs']}")
            print(f"  Trace 1 Output: {tracker.traces[0]['outputs']}")
            print("✅ Trace capture successful!")
        else:
            print("❌ Trace capture failed!")

if __name__ == "__main__":
    test_trace_capture()

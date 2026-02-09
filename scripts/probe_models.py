import os
import sys
from dotenv import load_dotenv

# Ensure the root directory is in the path
sys.path.append("/Users/govindmittal/datascience-setup/interview_prep/gartner")

from gss_agent.data.llm_config import llm_rotator, OPENROUTER_MODELS

def main():
    print(f"Testing LLM Rotator with {len(OPENROUTER_MODELS)} models + ZAI fallback...")
    
    # Test a few models
    for i in range(3):
        print(f"\n--- Request {i+1} ---")
        try:
            response = llm_rotator.generate(
                prompt="Say 'Model test successful' in 5 words.",
                system_prompt="Test assistant"
            )
            print(f"Response: {response}")
        except Exception as e:
            print(f"Request {i+1} failed: {e}")

if __name__ == "__main__":
    main()

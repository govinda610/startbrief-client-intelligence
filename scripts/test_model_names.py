#!/usr/bin/env python3
"""Test different model name variations for ZAI"""
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

def test_model(model_name):
    """Test a specific model name"""
    api_key = os.getenv("ZAI_API_KEY")
    zai_endpoint = "https://api.z.ai/api/anthropic"
    
    print(f"\n{'='*60}")
    print(f"Testing model: {model_name}")
    print(f"{'='*60}")
    
    try:
        client = OpenAI(api_key=api_key, base_url=zai_endpoint)
        
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": "Say hello"}],
            max_tokens=20
        )
        
        print(f"✅ SUCCESS with {model_name}!")
        if response.choices:
            print(f"Response: {response.choices[0].message.content}")
            return True
        else:
            print(f"Response structure: {response}")
            return False
            
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False

if __name__ == "__main__":
    # Try different model name variations
    model_variations = [
        "glm-4.7-flash",
        "GLM-4.7-Flash",
        "glm-4-7-flash",
        "glm4.7-flash",
        "GLM-4.7",
        "glm-4.7",
        "claude-3-5-sonnet-20241022",  # Try default Claude model
        "claude-3-5-sonnet-latest",
    ]
    
    print("Testing ZAI API with different model names...")
    
    for model in model_variations:
        result = test_model(model)
        if result:
            print(f"\n🎉 Found working model: {model}")
            break

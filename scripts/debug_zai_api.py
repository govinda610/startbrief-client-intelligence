#!/usr/bin/env python3
"""Debug script to inspect ZAI API response structure"""
import os
import sys
from dotenv import load_dotenv
from openai import OpenAI
import json

load_dotenv()

def debug_zai_api():
    """Debug ZAI GLM API response"""
    api_key = os.getenv("ZAI_API_KEY")
    
    if not api_key:
        print("❌ ZAI_API_KEY not found in .env")
        return False
    
    print(f"API Key: {api_key[:10]}...{api_key[-4:]}")
    
    zai_endpoint = "https://api.z.ai/api/anthropic"
    print(f"Endpoint: {zai_endpoint}")
    print(f"Model: glm-4.7-flash\n")
    
    try:
        client = OpenAI(
            api_key=api_key,
            base_url=zai_endpoint
        )
        
        print("Making request...")
        response = client.chat.completions.create(
            model="glm-4.7-flash",
            messages=[
                {"role": "user", "content": "Say hello"}
            ],
            max_tokens=20
        )
        
        print(f"\n✅ Request succeeded!")
        print(f"\nResponse object type: {type(response)}")
        print(f"\nResponse attributes: {dir(response)}")
        print(f"\nFull response: {response}")
        
        if hasattr(response, 'choices'):
            print(f"\nChoices: {response.choices}")
            if response.choices:
                print(f"First choice: {response.choices[0]}")
                if hasattr(response.choices[0], 'message'):
                    print(f"Message: {response.choices[0].message}")
                    if hasattr(response.choices[0].message, 'content'):
                        print(f"Content: {response.choices[0].message.content}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Request failed!")
        print(f"Error type: {type(e)}")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("ZAI API Debug")
    print("=" * 60 + "\n")
    debug_zai_api()

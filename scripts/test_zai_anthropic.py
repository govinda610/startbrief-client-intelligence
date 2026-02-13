import os
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

def test_zai_anthropic():
    api_key = os.getenv("ZAI_API_KEY")
    base_url = "https://api.z.ai/api/anthropic"
    
    # Test models
    models = ["glm-4.7", "glm-4.7-flash"]
    
    for model in models:
        print(f"\nTesting ZAI Anthropic with model: {model}")
        try:
            client = Anthropic(api_key=api_key, base_url=base_url)
            message = client.messages.create(
                model=model,
                max_tokens=100,
                messages=[
                    {"role": "user", "content": "Hello, are you working?"}
                ]
            )
            print(f"✅ SUCCESS with {model}!")
            print(f"Response: {message.content[0].text}")
        except Exception as e:
            print(f"❌ FAILED with {model}: {e}")

if __name__ == "__main__":
    test_zai_anthropic()

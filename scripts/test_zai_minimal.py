import os
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv

load_dotenv()

def test_zai_llm():
    print("Testing ZAI GLM-4.7 with ChatAnthropic...")
    api_key = os.getenv("ZAI_API_KEY")
    base_url = "https://api.z.ai/api/anthropic"
    
    llm = ChatAnthropic(
        model="glm-4.7",
        anthropic_api_key=api_key,
        base_url=base_url,
        max_tokens=1000
    )
    
    try:
        response = llm.invoke([HumanMessage(content="Explain quantum computing in 20 words.")])
        print(f"Success! Response: {response.content}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_zai_llm()

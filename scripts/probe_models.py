import os
import asyncio
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Exact list provided by user (Batch 2)
CANDIDATES = [
    "google/gemini-2.0-flash-exp:free",
    "openai/gpt-oss-120b:free",
    "openai/gpt-oss-20b:free"
]

async def probe(model):
    print(f"Probing {model}...")
    try:
        llm = ChatOpenAI(
            model=model,
            openai_api_key=OPENROUTER_API_KEY,
            openai_api_base="https://openrouter.ai/api/v1",
            max_tokens=50,
            request_timeout=30 
        )
        resp = await llm.ainvoke("Say 'ok'.")
        print(f"✅ {model} WORKS: {resp.content}")
        return model
    except Exception as e:
        print(f"❌ {model} FAILED: {str(e)[:100]}")
        return None

async def main():
    print(f"Testing {len(CANDIDATES)} candidates...")
    tasks = [probe(m) for m in CANDIDATES]
    results = await asyncio.gather(*tasks)
    working = [m for m in results if m]
    print(f"\nWORKING MODELS: {working}")

if __name__ == "__main__":
    asyncio.run(main())

import json
import os
import asyncio
import time
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv

load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

FREE_MODELS = [
    "nvidia/nemotron-3-nano-30b-a3b:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "tngtech/deepseek-r1t2-chimera:free",
    "z-ai/glm-4.5-air:free"
]

ABSTRACT_PROMPT = ChatPromptTemplate.from_template("""
Write a 2-sentence executive abstract for a Gartner Research report.
Title: "{title}"
Tags: {tags}
Value: {value}

Strictly professional tone. No markdown headers.
""")

async def fix_research():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    content_path = os.path.join(base_dir, "gss_agent/data/content.json")
    
    with open(content_path, "r") as f:
        data = json.load(f)
        
    # Process a subset (first 10) to save time/credits, as requested for verification
    subset = data[:10] 
    print(f"Regenerating abstracts for {len(subset)} research items...")
    
    llm = ChatOpenAI(
        model=FREE_MODELS[0],
        openai_api_key=OPENROUTER_API_KEY,
        openai_api_base="https://openrouter.ai/api/v1",
        max_tokens=150
    )

    for item in subset:
        print(f"Fixing: {item['title']}...")
        try:
            time.sleep(5) # Delay
            resp = await llm.ainvoke(ABSTRACT_PROMPT.format_messages(
                title=item['title'],
                tags=", ".join(item['tags']),
                value=item['strategic_value']
            ))
            item['abstract'] = resp.content
        except Exception as e:
            print(f"   Failed: {e}")

    # Save
    with open(content_path, "w") as f:
        json.dump(data, f, indent=2)
    print("Saved content.json")

    # Ingest
    print("Ingesting...")
    from gss_agent.rag.vector_store import GartnerVectorStore
    v_store = GartnerVectorStore(persist_directory=os.path.join(base_dir, "chroma_db"))
    v_store.ingest_research(content_path)
    print("Done.")

if __name__ == "__main__":
    asyncio.run(fix_research())

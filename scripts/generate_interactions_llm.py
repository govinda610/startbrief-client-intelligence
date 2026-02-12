import json
import os
import asyncio
import random
import time
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# --- VERIFIED FREE MODELS (As of Jan 2026) ---
FREE_MODELS = [
    "nvidia/nemotron-3-nano-30b-a3b:free",
    "tngtech/deepseek-r1t2-chimera:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "z-ai/glm-4.5-air:free"
]

# Strict rate limiting to avoid 429s on free tier
RATE_LIMIT_DELAY = 10.0 

TRANSCRIPT_PROMPT = ChatPromptTemplate.from_template("""
You are generating a realistic call transcript for a Nexus Advisory simulation.

Client: {client_name} ({company_name})
Industry: {industry}
Context: {scenario}

Output a dialogue between "Nexus Advisory Associate" and "{client_name}".
- The dialogue must be realistic, including complaints about budget or competitors.
- The client should be skeptical. 
- The Associate should be professional.
- Length: 10-15 lines.
- FORMAT: Just the dialogue. No intros/outros.
""")

async def generate_with_retry(client, scenario):
    attempts = 0
    max_attempts = 4
    
    while attempts < max_attempts:
        try:
            # Rotate models
            model = FREE_MODELS[attempts % len(FREE_MODELS)]
            print(f"   Using {model} for {client['name']}...")
            
            # Enforce Delay
            await asyncio.sleep(RATE_LIMIT_DELAY) 
            
            llm = ChatOpenAI(
                model=model,
                openai_api_key=OPENROUTER_API_KEY,
                openai_api_base="https://openrouter.ai/api/v1",
                max_tokens=800,
                request_timeout=60,
            )
            
            contact = client["key_contacts"][0]
            response = await llm.ainvoke(TRANSCRIPT_PROMPT.format_messages(
                client_name=contact["name"], 
                company_name=client["name"],
                industry=client["industry"],
                scenario=scenario
            ))
            
            content = response.content
            if len(content) < 50: raise ValueError("Response too short")

            return {
                "id": f"int_{client['id']}_{random.randint(10000, 99999)}",
                "client_id": client["id"],
                "client_name": client["name"],
                "date": "2025-02-15",
                "type": "Call Transcript",
                "summary": scenario,
                "content": content,
                "sentiment": client["churn_risk"],
                "actions_identified": ["Log Call", "Follow Up"]
            }
            
        except Exception as e:
            print(f"   Error: {str(e)[:100]}")
            attempts += 1
            await asyncio.sleep(5) 
            
    print(f"FAILED to generate for {client['name']}")
    return None

async def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    clients_path = os.path.join(base_dir, "gss_agent/data/clients.json")
    
    with open(clients_path, "r") as f:
        clients = json.load(f)
    
    tasks = []
    print(f"Starting generation for {len(clients)} clients with verified free models...")
    
    results = []
    for client in clients:
        # Generate 1 robust transcript per client
        scenario = f"Renewal discussion. {client['name']} is considering cutting budget due to {client['industry']} downturn."
        res = await generate_with_retry(client, scenario)
        if res: results.append(res)
    
    # Save
    output_path = os.path.join(base_dir, "gss_agent/data/generated_interactions_llm.json")
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Saved {len(results)} interactions to {output_path}")
    
    # Ingest
    if results:
        print("Ingesting into ChromaDB...")
        from gss_agent.rag.vector_store import NexusVectorStore
        v_store = NexusVectorStore(persist_directory=os.path.join(base_dir, "chroma_db"))
        v_store.ingest_interactions(output_path)
        print("Ingestion Complete.")

if __name__ == "__main__":
    asyncio.run(main())

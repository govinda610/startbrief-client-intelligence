import json
import os
import random
from typing import List
from pydantic import BaseModel, Field
from gss_agent.data.llm_config import llm_rotator

DATA_DIR = "/Users/govindmittal/datascience-setup/interview_prep/gartner/gss_agent/data"
OUTPUT_FILE = os.path.join(DATA_DIR, "content.json")

RESEARCH_TYPES = [
    "Magic Quadrant",
    "Hype Cycle",
    "Critical Capabilities",
    "Quick Answer",
    "Peer Insights",
    "Market Guide"
]

TOPICS = [
    "Customer Data Platforms", "Sales Force Automation", "Cloud AI Development",
    "Generative AI", "CRM Systems", "Data Analytics", "Security Operations",
    "Enterprise Networking", "Supply Chain Management", "Digital Transformation"
]

class ResearchItem(BaseModel):
    title: str = Field(..., description="Research report title")
    abstract: str = Field(..., description="Detailed 300-500 word abstract")
    strategic_value: str = Field(..., description="Value proposition")

class ResearchBatch(BaseModel):
    items: List[ResearchItem]

def generate_research_batch(count: int = 5):
    """Generate research items with detailed abstracts"""
    prompt = f"""
Generate {count} realistic Nexus Advisory research reports. Return ONLY valid JSON in this exact format:

{{
  "items": [
    {{
      "title": "Magic Quadrant for Customer Data Platforms, 2025",
      "abstract": "The 2025 Magic Quadrant for Customer Data Platforms (CDPs) highlights a market in rapid transition as organizations prioritize unified data foundations for generative AI. Key findings indicate that successful vendors are increasingly integrating native AI capabilities and enhancing real-time activation workflows. The research evaluates 18 vendors on completeness of vision and ability to execute, noting that scalability and data governance remain critical differentiators. Implementation considerations should focus on data quality and identity resolution accuracy to maximize ROI, which is projected at 12-18% through improved marketing efficiency...",
      "strategic_value": "Increases sales productivity by 15% through unified customer views"
    }}
  ]
}}

Research types: Magic Quadrant, Hype Cycle, Critical Capabilities, Quick Answer, Peer Insights, Market Guide
Topics: {', '.join(random.sample(TOPICS, min(5, len(TOPICS))))}

Make each abstract 350-500 words, providing a comprehensive professional analysis including market dynamics, vendor landscape, and strategic recommendations.
"""
    
    system_prompt = "You are a Nexus Advisory research analyst. You provide deep technical and strategic insights. Return ONLY valid JSON with no preamble."
    
    try:
        batch = llm_rotator.generate_structured(prompt, ResearchBatch, system_prompt, max_tokens=6000)
        return batch.items
    except Exception as e:
        print(f"Error generating research batch: {e}")
        return []

def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # Load existing content if any
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r") as f:
            all_research = json.load(f)
        print(f"Loaded {len(all_research)} existing research items")
    else:
        all_research = []
    
    target_count = 100
    
    print(f"Generating research content (target: {target_count})...")
    
    while len(all_research) < target_count:
        batch_size = min(5, target_count - len(all_research))
        batch = generate_research_batch(batch_size)
        
        for idx, item in enumerate(batch):
            research_id = f"RES-{len(all_research) + 2000}"
            
            # Generate publication date (2024-2025)
            year = random.choice([2024, 2025])
            month = random.randint(1, 12)
            day = random.randint(1, 28)
            
            # Random topics
            num_tags = random.randint(2, 4)
            tags = random.sample(["GenAI", "CRM", "Cloud", "Data", "Sales Ops", "Security"], num_tags)
            
            # Mark some for evaluation
            is_evaluation_target = (len(all_research) + idx) < 20
            
            research = {
                "id": research_id,
                "title": item.title,
                "abstract": item.abstract,
                "strategic_value": item.strategic_value,
                "tags": tags,
                "published_date": f"{year:04d}-{month:02d}-{day:02d}",
                "evaluation_metadata": {
                    "is_target": is_evaluation_target,
                    "evaluation_id": f"EVAL-RES-{idx:03d}" if is_evaluation_target else None
                }
            }
            all_research.append(research)
            
            if len(all_research) >= target_count:
                break
        
        # Save after each batch
        with open(OUTPUT_FILE, "w") as f:
            json.dump(all_research, f, indent=2)
        print(f"Batch saved. Total items: {len(all_research)}")
    
    print(f"✅ Successfully generated {len(all_research)} research items in {OUTPUT_FILE}")

if __name__ == "__main__":
    main()

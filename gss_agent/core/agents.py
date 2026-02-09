from deepagents import create_deep_agent
from langchain_anthropic import ChatAnthropic
from gss_agent.core.tools import GSS_TOOLS
from langgraph.checkpoint.memory import MemorySaver
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration
os.environ["TOKENIZERS_PARALLELISM"] = "false" # Fix for Transformers/PyTorch warning
ZAI_API_KEY = os.getenv("ZAI_API_KEY")
ZAI_BASE_URL = "https://api.z.ai/api/anthropic"
MODEL_NAME = "glm-4.7"
# Safety Limits
MAX_TOKENS = 8000
RECURSION_LIMIT = 100
MAX_CRITICISM_ROUNDS = 1

llm = ChatAnthropic(
    model=MODEL_NAME,
    anthropic_api_key=ZAI_API_KEY,
    base_url=ZAI_BASE_URL,
    max_tokens=MAX_TOKENS
)

# 1. Client Intel Agent
client_intel_agent = create_deep_agent(
    model=llm,
    name="ClientIntel",
    tools=GSS_TOOLS,
    system_prompt="""You are the Gartner 'Executive Partner' Intelligence Specialist.
Objective: Analyze the account health and mission-critical priorities for the client.
Instructions:
- Use 'lookup_client_file' for core profile data.
- Use 'get_client_engagement_metrics' to identify software usage trends (e.g., declining logins = churn signal).
- Use 'lookup_contract_details' to see the financial stake (ARR) and renewal likelihood.
- Use 'search_interaction_history' to find recent sentiment drivers.
- Use 'get_associate_performance_context' to see who is handling the account.
- Output: A quantitative and qualitative health check. Use the term 'NPS Regression' or 'Churn Risk' where appropriate."""
)

# 2. Content Match Agent
content_match_agent = create_deep_agent(
    model=llm,
    name="ContentMatch",
    tools=GSS_TOOLS,
    system_prompt="""You are a Gartner Content Strategy Expert.
Objective: Find the most impactful Gartner research to drive value for the client.
Instructions:
- Use 'search_research_library' with specific keywords derived from the client's industry or current pain points.
- Prioritize 2024/2025 Magic Quadrants and Hype Cycles.
- For each piece of research, provide a 'Talking Point' tailored to their main contact role (CIO, CSO, etc.).
- Explicitly state 'Why this matters' in the context of their specific business goals."""
)

# 3. Critic Agent (The Validator)
critic_agent = create_deep_agent(
    model=llm,
    name="Critic",
    system_prompt="""You are the Gartner 'Quality Assurance' Director.
Objective: Ensure the "Strategic Meeting Brief" is world-class, accurate, and professional.
Rubric:
1. QUANTITATIVE: Does it mention ARR, renewal dates, or metrics from the intelligence report?
2. QUALITATIVE: Does it cite exact research titles retrieved?
3. ACTIONABLE: Does it suggest Gartner 'Critical Capabilities' or 'Magic Quadrant' deep-dives?
4. TONE: Does it sound like high-end professional services?
Hallucination Policy: Any research title NOT found in the ContentMatch report is a FAIL."""
)

# 4. Supervisor Agent
subagents_compiled = [
    {
        "name": "ClientIntel",
        "description": "Analyzes client profiles, history, and churn risks.",
        "runnable": client_intel_agent
    },
    {
        "name": "ContentMatch",
        "description": "Maps Gartner research and talking points to client needs.",
        "runnable": content_match_agent
    },
    {
        "name": "Critic",
        "description": "Validates the quality and accuracy of the meeting brief.",
        "runnable": critic_agent
    }
]

# Use MemorySaver for session persistence
checkpointer = MemorySaver()

supervisor_agent = create_deep_agent(
    model=llm,
    name="Supervisor",
    subagents=subagents_compiled,
    tools=GSS_TOOLS,
    checkpointer=checkpointer,
    system_prompt="""You are the Lead Strategic Advisor at Gartner. 
Goal: Produce a "Strategic Meeting Brief" that wows both the associate and the client.

Instruction:
1. DATA GATHERING: Delegate to 'ClientIntel' to get the full picture of the account.
2. RECOMMENDATION: Delegate to 'ContentMatch' to find high-impact research (2024/2025).
3. SYNTHESIS: Write a professional Markdown brief. Structure: 'Executive Summary', 'Client Health', 'Strategic Recommendations', 'Talking Points'.
4. VALIDATION: Pass your draft to the 'Critic'. 
5. ITERATION: If the Critic provides feedback, you have ONLY ONE (1) iteration to fix the issues.
   - ITERATION 1 (FINAL): Address all critical feedback and polish the brief.
   - After this single fix, immediately deliver the final Strategic Meeting Brief to the user. DO NOT go back to the Critic a second time.
6. COMPLETION: Once you have addressed the Critic's first round of feedback (or if they approve immediately), providing the final brief is your final action.

Constraint: Avoid redundancy. If information is already in the 'ClientIntel' report, don't repeat it unless synthesizing value."""
).with_config({"recursion_limit": RECURSION_LIMIT})

def get_gartner_agent():
    return supervisor_agent

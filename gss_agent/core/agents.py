from deepagents import create_deep_agent
from langchain_openai import ChatOpenAI
from gss_agent.core.tools import GSS_TOOLS
from langgraph.checkpoint.memory import MemorySaver
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL_NAME = "minimax/minimax-m2.1"
# Safety Limits
MAX_TOKENS = 4000
RECURSION_LIMIT = 50

llm = ChatOpenAI(
    model=MODEL_NAME,
    openai_api_key=OPENROUTER_API_KEY,
    openai_api_base="https://openrouter.ai/api/v1",
    max_tokens=MAX_TOKENS
)

# 1. Client Intel Agent
client_intel_agent = create_deep_agent(
    model=llm,
    name="ClientIntel",
    tools=GSS_TOOLS,
    system_prompt="""You are a Gartner Client Intelligence Expert.
Objective: Provide a deep-dive analysis of the client's current status and churn risk.
Inputs: You have access to client registry and interaction history.
Instructions:
- Use 'lookup_client_file' to understand the client's industry, revenue, and entitlements (e.g., GSL, GSSO).
- Use 'search_interaction_history' to find recent high-stakes conversations or negative sentiment.
- If usage data is present in interactions, use 'analyze_data_python' to calculate growth/drop trends.
- Output a structured summary: 'Client Context', 'Engagement Health', and 'Identified Risks'."""
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
    system_prompt="""You are the Gartner Quality Assurance Critic.
Objective: Ensure the "Strategic Meeting Brief" is world-class and hallucination-free.
Rubric:
1. RELEVANCE: Does it use the specific client industry and revenue data?
2. ACCURACY: Are the research titles exact matches to what was retrieved? (Hallucination is a fail).
3. ACTIONABILITY: Are there at least 3 concrete conversation starters?
4. TONE: Does it sound like a premium Gartner advisor? (Blue-chip, strategic, concise).

Feedback Loop:
- If the brief passes all criteria, respond ONLY with "APPROVED".
- If it fails, provide a bulleted list of fixes for the Supervisor."""
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

Operational Workflow:
1. DATA GATHERING: Delegate to 'ClientIntel' to get the full picture of the account.
2. RECOMMENDATION: Delegate to 'ContentMatch' to find high-impact research (2024/2025).
3. SYNTHESIS: Write a professional Markdown brief. Structure: 'Executive Summary', 'Client Health', 'Strategic Recommendations', 'Talking Points'.
4. VALIDATION: Pass your draft to the 'Critic'. 
5. ITERATION: If the Critic provides feedback, use your tools again if necessary to fix the issues.
6. COMPLETION: Once the Critic says "APPROVED", provide the final brief to the user.

Constraint: Avoid redundancy. If information is already in the 'ClientIntel' report, don't repeat it unless synthesizing value."""
).with_config({"recursion_limit": RECURSION_LIMIT})

def get_gartner_agent():
    return supervisor_agent

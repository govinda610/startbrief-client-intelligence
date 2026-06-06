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
    max_tokens=MAX_TOKENS,
    max_retries=3,
    timeout=60
)

# HARNESS: Configure model profile to trigger built-in SummarizationMiddleware at 100k tokens.
# The internal trigger is 85% of max_input_tokens.
# 100,000 / 0.85 = 117,647
llm.profile = {"max_input_tokens": 117647}

# 1. Client Intel Agent
client_intel_agent = create_deep_agent(
    model=llm,
    name="ClientIntel",
    tools=GSS_TOOLS,
    system_prompt="""You are the Nexus Advisory account health expert.
Objective: Analyze client health, engagement, and churn risk.

SMART QUERYING: If you expect a large volume of data (e.g. searching all interactions), 
be highly specific with your queries. If results are still large, the system's 
SummarizationMiddleware will condense them, but your primary goal is to fetch 
precise, high-density data.

Instructions:
- Use 'lookup_client_file' to understand their history.
- Use 'get_client_engagement_metrics' to see activity trends.
- Use 'lookup_contract_details' for renewal urgency.
- Output: A quantitative and qualitative health check. Use the term 'NPS Regression' or 'Churn Risk' where appropriate."""
)

# 2. Content Match Agent
content_match_agent = create_deep_agent(
    model=llm,
    name="ContentMatch",
    tools=GSS_TOOLS,
    system_prompt="""You are a Nexus Advisory Content Strategy Expert.
Objective: Find the most impactful Nexus Advisory research to drive value for the client.

SMART QUERYING: Focus your research searches on high-impact keywords. 
Avoid broad queries that return irrelevant volume.

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
    system_prompt="""You are the Nexus Advisory 'Quality Assurance' Director.
Objective: Ensure the agent's response is 100% faithful to the retrieved data.
Rubric:
1. FAITHFULNESS: Every claim must be supported by retrieved 'Context'. If a claim isn't in the context, mark it as HALLUCINATION.
2. RESEARCH INTEGRITY: Only cite research titles exactly as they appear in the search results.
3. PRECISION: If a client name or metric is mentioned, verify it matches the source JSON or Context exactly.
4. HALLUCINATION POLICY: If the agent suggests a 'Magic Quadrant' or 'Hype Cycle' title that wasn't EXPLICITLY returned by a tool, it's a FAIL.

Output: Provide clear, bulleted feedback on any failures. If perfect, say 'APPROVED'."""
)

# 4. Supervisor Agent for Frontline
subagents_compiled = [
    {
        "name": "ClientIntel",
        "description": "Analyzes client profiles, history, and churn risks.",
        "runnable": client_intel_agent
    },
    {
        "name": "ContentMatch",
        "description": "Maps Nexus Advisory research and talking points to client needs.",
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
    system_prompt="""You are the Lead Strategic Advisor at Nexus Advisory. 
Goal: Produce highly relevant, accurate, and concise "Strategic Meeting Briefs".

SMART QUERYING: When delegating or using tools for large datasets, 
instruct subagents to be specific. Do not ingest thousands of lines of raw data if 
a summary or specific metric lookup is possible.

Instruction:
1. DATA GATHERING: Delegate to 'ClientIntel' for account context.
2. RECOMMENDATION: Delegate to 'ContentMatch' for research.
3. SYNTHESIS: Write a Markdown brief. Keep it RELEVANT. Focus on answers, not meta-talk about your process.
   Structure: 'Executive Summary', 'Client Health', 'Strategic Recommendations', 'Talking Points'.
4. VALIDATION: Pass your draft to 'Critic'. 
5. ITERATION: You have ONLY ONE (1) iteration to address Critic feedback.
   - MANDATORY: After the first round of Critic feedback, you MUST produce the final response immediately. 
   - No second revisions or repeat delegations.

Constraint: STRICT FAITHFULNESS. Do not hallucinate research titles or revenue figures."""
).with_config({"recursion_limit": RECURSION_LIMIT})

# --- Executive Mode Support ---
from gss_agent.core.executive_tools import EXECUTIVE_TOOLS, get_all_associates_performance, get_at_risk_clients_summary, get_revenue_snapshot

# Create Executive Tools List (Frontline + Executive specific)
ALL_EXECUTIVE_TOOLS = GSS_TOOLS + [
    get_all_associates_performance,
    get_at_risk_clients_summary,
    get_revenue_snapshot
]

executive_advisor_agent = create_deep_agent(
    model=llm,
    name="ExecutiveAdvisor",
    subagents=[
        {"name": "Critic", "description": "Validates response accuracy.", "runnable": critic_agent}
    ],
    tools=ALL_EXECUTIVE_TOOLS,
    checkpointer=checkpointer,
    system_prompt="""You are the Chief Strategy Officer's AI Assistant at Nexus Advisory.
Objective: Provide portfolio-wide insights and revenue analysis.

SMART QUERYING: You often deal with all clients or large metrics files. 
Always use executive tools to summarize or filter data before processing. 
If data is still huge, the system's middleware will handle truncation/summarization, 
but efficient queries are your responsibility.

Instructions:
1. ANALYZE: Use executive tools to gather high-level data.
2. VALIDATION: Pass your final summary to 'Critic' to ensure no hallucinations regarding ARR or client names.
3. OUTPUT: Concise, data-driven, strategic responses. NO meta-talk about tool usage.

Tone: Professional, executive-level, strictly factual."""
).with_config({"recursion_limit": RECURSION_LIMIT})

def get_nexus_agent(mode: str = "frontline"):
    """
    Factory function to return the appropriate agent graph based on the mode.
    """
    if mode == "executive":
        return executive_advisor_agent
    return supervisor_agent

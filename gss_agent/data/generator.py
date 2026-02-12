import json
import random
from faker import Faker
import os

fake = Faker()

# Real Nexus Advisory Context Data
REAL_CLIENTS = [
    {"name": "Amazon", "industry": "Technology/E-commerce", "revenue": "$570B", "region": "Global"},
    {"name": "Centers for Medicare & Medicaid Services (CMS)", "industry": "Government/Healthcare", "revenue": "N/A", "region": "North America"},
    {"name": "David's Bridal", "industry": "Retail", "revenue": "$1B+", "region": "North America"},
    {"name": "GEP Worldwide", "industry": "Supply Chain/Software", "revenue": "$1B+", "region": "Global"},
    {"name": "Akamai Technologies", "industry": "Cloud Computing/Security", "revenue": "$3.8B", "region": "Global"},
    {"name": "Salesforce", "industry": "SaaS/CRM", "revenue": "$34B", "region": "Global"},
    {"name": "Tealium", "industry": "Data/Marketing", "revenue": "$200M+", "region": "North America"},
    {"name": "Databricks", "industry": "Data/AI", "revenue": "$1.5B+", "region": "Global"}
]

NEXUS_ENTITLEMENTS = [
    "Nexus Advisory for Sales Leaders (GSL)",
    "Nexus Advisory for Technology CSOs",
    "Nexus Advisory for Marketing Leaders",
    "Nexus Advisory Global Sales Strategy & Operations (GSSO) Advisory",
    "Sales Score Diagnostic",
    "Comparative Seller Performance Diagnostic",
    "Nexus Advisory BuySmart",
    "Nexus Advisory Digital Markets"
]

RESEARCH_TITLES = [
    "Magic Quadrant for Cloud Database Management Systems 2024",
    "Magic Quadrant for Customer Data Platforms (CDPs) 2024",
    "Hype Cycle for Emerging Technologies 2024",
    "Hype Cycle for Revenue and Sales Technology 2024",
    "Top 10 Strategic Technology Trends for 2025: Agentic AI",
    "Predicts 2025: The Rise of Machine Sellers",
    "Designing Optimal Territory Investment for 2025",
    "Digital Twins of the Customer: Driving Hyper-Personalization",
    "Emotion AI in B2B Sales: The Next Frontier",
    "Critical Capabilities for Sales Force Automation 2024",
    "Innovation Insight for Agentic AI in Sales",
    "Quick Answer: How to Use GenAI for Territory Planning"
]

STRATEGIC_ACTIONS = [
    "Recommend content push for re-engagement",
    "Flag for account manager: Competitor Mention",
    "Executive Outreach: Low Feature Utilization",
    "Recommend training on Sales Score tool",
    "Cross-sell: Upgrade to GSSO Advisory",
    "Renewal Prep: Value Realization Review"
]

def generate_clients(n=20):
    clients = []
    for i in range(n):
        if i < len(REAL_CLIENTS):
            base = REAL_CLIENTS[i]
        else:
            base = {
                "name": fake.company(),
                "industry": fake.bs(),
                "revenue": f"${random.randint(100, 999)}M",
                "region": random.choice(["North America", "EMEA", "APAC", "LATAM"])
            }
        
        client = {
            "id": f"CL-{1000+i}",
            "name": base["name"],
            "industry": base["industry"],
            "revenue": base["revenue"],
            "region": base["region"],
            "subscription_tier": random.choice(["Enterprise", "Global", "Professional"]),
            "entitlements": random.sample(NEXUS_ENTITLEMENTS, k=random.randint(1, 3)),
            "retention_risk": random.choice(["Low", "Medium", "High"]),
            "churn_signals": random.sample([
                "Low login frequency (last 30 days)",
                "Negative sentiment in support tickets",
                "Competitor mentioned in recent inquiry",
                "Decision maker left the company",
                "Unsubscribed from weekly digest"
            ], k=random.randint(0, 2)),
            "main_contact_role": random.choice(["CIO", "CMO", "CSO", "VP Sales", "Director of Strategy"])
        }
        clients.append(client)
    return clients

def generate_content(n=50):
    content = []
    for i in range(n):
        title = random.choice(RESEARCH_TITLES) if i < len(RESEARCH_TITLES) else f"{fake.catch_phrase()} Report 2025"
        item = {
            "id": f"RES-{2000+i}",
            "title": title,
            "abstract": fake.paragraph(nb_sentences=5),
            "strategic_value": random.choice([
                "Increases sales productivity by 15%",
                "Helps in cloud migration cost-saving",
                "Improves customer retention via personalization",
                "Identifies key AI vendors for 2025"
            ]),
            "tags": random.sample(["GenAI", "Sales Ops", "Strategy", "Cloud", "Data", "CRM"], k=3),
            "published_date": fake.date_this_year().isoformat()
        }
        content.append(item)
    return content

def generate_interactions(clients, n=100):
    interactions = []
    for i in range(n):
        client = random.choice(clients)
        interaction = {
            "id": f"INT-{3000+i}",
            "client_id": client["id"],
            "client_name": client["name"],
            "date": fake.date_this_year().isoformat(),
            "type": random.choice(["Meeting Note", "Support Ticket", "Inquiry Call", "Email"]),
            "summary": fake.sentence(nb_words=15),
            "sentiment": random.choice(["Positive", "Neutral", "Negative"]),
            "actions_identified": random.sample(STRATEGIC_ACTIONS, k=random.randint(1, 2))
        }
        interactions.append(interaction)
    return interactions

if __name__ == "__main__":
    # Ensure relative paths work if script is run from project root
    dir_path = os.path.dirname(os.path.realpath(__file__))
    
    clients = generate_clients(20)
    content = generate_content(50)
    interactions = generate_interactions(clients, 100)
    
    with open(os.path.join(dir_path, "clients.json"), "w") as f:
        json.dump(clients, f, indent=4)
    with open(os.path.join(dir_path, "content.json"), "w") as f:
        json.dump(content, f, indent=4)
    with open(os.path.join(dir_path, "interactions.json"), "w") as f:
        json.dump(interactions, f, indent=4)
        
    print(f"Generated {len(clients)} clients, {len(content)} papers, {len(interactions)} interactions.")

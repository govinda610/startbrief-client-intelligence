import json
import random
from faker import Faker
import datetime

fake = Faker()

# Templates for dialogue segments
GREETINGS_ASSOCIATE = [
    "Hi {client_name}, thanks for joining me today.",
    "Good morning {client_name}, I wanted to touch base on your renewal.",
    "Hello {client_name}, great to connect. How are things at {company}?"
]

GREETINGS_CLIENT = [
    "Hi, thanks for setting this up.",
    "Good morning. I have a hard stop in 30 minutes.",
    "Hey. We're pretty busy with Q1 planning, so let's keep this brief."
]

PAIN_POINTS = [
    "We're struggling to get adoption for our new sales tool.",
    "Our cloud costs are spiraling out of control.",
    "I'm worried about the incoming regulations on AI usage.",
    "We need to cut our vendor spend by 10% this year.",
    "My team doesn't know how to sell against our new competitor."
]

GARTNER_PITCH = [
    "Have you seen our latest Magic Quadrant on this?",
    "I can set up an inquiry with an analyst who covers exactly that.",
    "We have a tool called the 'Sales Score' that diagnoses this issue.",
    "Our 'BuySmart' service can review that contract for you."
]

OBJECTIONS = [
    "I'm not sure we're getting enough value from the subscription.",
    "Your research feels a bit generic for our niche.",
    "We simply don't have the budget to renew at this level.",
    "I haven't logged in for three months."
]

CLOSING = [
    "Let me send you that report and we can follow up next week.",
    "I'll book that analyst call for you right away.",
    "Let's schedule a deeper dive with your team."
]

def generate_transcript(client_name, company_name, sentiment="neutral"):
    dialogue = []
    
    # Intro
    dialogue.append(f"Gartner Associate: {random.choice(GREETINGS_ASSOCIATE).format(client_name=client_name, company=company_name)}")
    dialogue.append(f"{client_name} ({company_name}): {random.choice(GREETINGS_CLIENT)}")
    
    # Discussion
    pain = random.choice(PAIN_POINTS)
    dialogue.append(f"{client_name} ({company_name}): {pain}")
    
    pitch = random.choice(GARTNER_PITCH)
    dialogue.append(f"Gartner Associate: That sounds challenging. {pitch}")
    
    if sentiment == "negative":
        objection = random.choice(OBJECTIONS)
        dialogue.append(f"{client_name} ({company_name}): To be honest, {objection}")
        dialogue.append("Gartner Associate: I understand. Let's look at a usage plan to fix that.")
    else:
        dialogue.append(f"{client_name} ({company_name}): That would be helpful. Can you send me the link?")
        
    # Closing
    dialogue.append(f"Gartner Associate: {random.choice(CLOSING)}")
    
    return "\n".join(dialogue)

def main():
    clients = [
        {"name": "Andy Jassy", "company": "Amazon", "sentiment": "neutral"},
        {"name": "Tom Leighton", "company": "Akamai", "sentiment": "negative"},
        {"name": "CIO", "company": "CMS", "sentiment": "positive"},
        {"name": "CMO", "company": "GEP", "sentiment": "positive"}
    ]
    
    transcripts = []
    for _ in range(10): # Generate 10 variations
        client = random.choice(clients)
        transcript = generate_transcript(client["name"], client["company"], client["sentiment"])
        transcripts.append({
            "client_id": f"c_{client['company'].lower()[:3]}_001" if client['company'] != "Akamai" else "c_aka_002", # Simplified mapping
            "date": (datetime.datetime.now() - datetime.timedelta(days=random.randint(1, 90))).strftime("%Y-%m-%d"),
            "content": transcript,
            "metadata": {"sentiment": client["sentiment"]}
        })
        
    with open("gss_agent/data/generated_transcripts.json", "w") as f:
        json.dump(transcripts, f, indent=2)
    
    print(f"Generated {len(transcripts)} transcripts in gss_agent/data/generated_transcripts.json")

if __name__ == "__main__":
    main()

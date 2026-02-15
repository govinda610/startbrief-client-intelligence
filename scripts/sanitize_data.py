import json
import os

def sanitize_text(text):
    if not isinstance(text, str):
        return text
    # Replace common garbled placeholders
    replacements = {
        "\u2014": " - ",
        "\u201d": '"',
        "\u201c": '"',
        "\u2019": "'",
        "\u00a0": " ",
        "  ": " "
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text

def sanitize_json(file_path):
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return
    
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                for key, value in item.items():
                    if isinstance(value, str):
                        item[key] = sanitize_text(value)
                    elif isinstance(value, list):
                        item[key] = [sanitize_text(v) if isinstance(v, str) else v for v in value]
    
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Sanitized {file_path}")

DATA_DIR = "/Users/govindmittal/datascience-setup/interview_prep/gartner/gss_agent/data"
sanitize_json(os.path.join(DATA_DIR, "interactions.json"))
sanitize_json(os.path.join(DATA_DIR, "content.json"))

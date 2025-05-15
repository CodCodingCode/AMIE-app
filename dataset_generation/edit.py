import json

# Load JSONL file (one JSON object per line)
with open("datasets/combined_dataset.jsonl", "r") as f:
    data = [json.loads(line) for line in f]


# Function to edit instruction
def edit_instruction():
    return "You are a medical expert. You are given a doctor's vignette and your job is to generate the best possible question to ask the patient to help lead to the correct diagnosis."


# Modify the "instruction" field
for entry in data:
    if "instruction" in entry:
        entry["instruction"] = edit_instruction()

# Save modified JSONL
with open("edited_file.jsonl", "w") as f:
    for entry in data:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

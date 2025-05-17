import re
import json
import os

# Define paths to the JSON files
files = {
    "You are simulating a real patient in conversation with their doctor.": "all_patient_followups.json",
    "You are a clinical summarizer trained to extract structured vignettes from doctor–patient dialogues.": "all_summarizer_outputs.json",
    "You are a board-certified diagnostician that diagnoses patients.": "all_diagnosing_doctor_outputs.json",
    "You are a physician asking questions to diagnose a patient.": "all_questioning_doctor_outputs.json",
}

combined_data = []

# Load and reformat each file
for instruction, filename in files.items():
    if not os.path.exists(filename):
        print(f"File not found: {filename}")
        continue
    with open(filename, "r") as f:
        entries = json.load(f)
        for entry in entries:
            combined_data.append({
                "instruction": instruction,
                "input": re.sub(r"^\s*\d+\.\s*", "", entry.get("input", "")),
                "output": entry.get("output", "")
            })

# Save combined output
with open("combined_conversations.json", "w") as f:
    json.dump(combined_data, f, indent=2)

print("✅ Combined JSON written to combined_conversations.json")
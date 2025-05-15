import json

# Load your JSON file
with open("dataset_generation/results.json", "r") as f:
    cases = json.load(f)

# Convert to input/output format
converted = []
for case in cases:
    new_entry = {
        "instruction": "You are a medical expert. You are given a doctor's vignette and your job is to generate the top ten diagnoses for the patient.",
        "input": case["doctor_vignette"],
        "output": case["diseases"],  # this is a list of 10 potential diseases
    }
    converted.append(new_entry)

# Save to a new JSON file
with open("vignette_to_diseases.json", "w") as f:
    json.dump(converted, f, indent=2, ensure_ascii=False)

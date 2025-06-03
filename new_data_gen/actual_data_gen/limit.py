import json

with open("patient_roleplay_scripts.json", "r") as f:
    data = json.load(f)

count = 0
if "roleplay_scripts" in data:
    for disease, scripts in data["roleplay_scripts"].items():
        if isinstance(scripts, list):
            count += len(scripts)
            print(f"{disease}: {len(scripts)} vignettes")

print(f"Total: {count} vignettes")

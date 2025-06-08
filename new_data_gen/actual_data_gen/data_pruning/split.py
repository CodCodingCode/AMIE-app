import json
import os

# Find JSON file in current directory
json_files = [
    "all_questioning_doctor_outputs.json",
    "all_diagnosing_doctor_outputs.json",
]

if not json_files:
    print("No JSON files found")
    exit()

if len(json_files) == 1:
    input_file = json_files[0]
else:
    print("Multiple JSON files found:")
    for i, f in enumerate(json_files):
        print(f"{i+1}. {f}")
    choice = int(input("Choose file (number): ")) - 1
    input_file = json_files[choice]

# Load and split
with open(input_file, "r") as f:
    data = json.load(f)

groups = {"E": [], "M": [], "L": []}

for entry in data:
    letter = entry.get("letter")
    if letter in groups:
        groups[letter].append(entry)

# Save files
for letter, entries in groups.items():
    if entries:
        output_file = f"{letter}D.json"
        with open(output_file, "w") as f:
            json.dump(entries, f, indent=2)
        print(f"Saved {len(entries)} entries to {output_file}")

print("Done")

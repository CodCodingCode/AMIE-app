import os
import json

# Define the folders and their corresponding output filenames
folders = {
    "diagnosing_doctor_outputs": "all_diagnosing_doctor_outputs.json",
    "patient_followups": "all_patient_followups.json",
    "questioning_doctor_outputs": "all_questioning_doctor_outputs.json",
    "summarizer_outputs": "all_summarizer_outputs.json",
}

for folder, output_file in folders.items():
    all_data = []

    # Go through each .json file in the folder
    for filename in os.listdir(folder):
        if filename.endswith(".json"):
            filepath = os.path.join(folder, filename)
            try:
                with open(filepath, "r") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        all_data.extend(data)
                    elif isinstance(data, dict):
                        all_data.append(data)
            except Exception as e:
                print(f"Failed to load {filepath}: {e}")

    # Save the combined output
    with open(output_file, "w") as f:
        json.dump(all_data, f, indent=2)

    print(f"✅ Merged {len(all_data)} entries from '{folder}' into '{output_file}'")

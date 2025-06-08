import os
import json

# Normalize script directory for relative paths
script_dir = os.path.dirname(os.path.abspath(__file__))


def main():
    # Define the folders and their corresponding output filenames with normalized paths
    folders = {
        os.path.join(
            script_dir, "..", "..", "..", "2diagnosing_doctor_outputs"
        ): "all_diagnosing_doctor_outputs.json",
        os.path.join(
            script_dir, "..", "..", "..", "2patient_followups"
        ): "all_patient_followups.json",
        os.path.join(
            script_dir, "..", "..", "..", "2questioning_doctor_outputs"
        ): "all_questioning_doctor_outputs.json",
        os.path.join(
            script_dir, "..", "..", "..", "2summarizer_outputs"
        ): "all_summarizer_outputs.json",
        os.path.join(
            script_dir, "..", "..", "..", "2treatment_plans"
        ): "all_treatment_outputs.json",
        os.path.join(
            script_dir, "..", "..", "..", "2behavioral_analyses"
        ): "all_behavioral_analyses.json",
    }

    for folder, output_file in folders.items():
        all_data = []

        # Error handling for missing folder
        if not os.path.exists(folder):
            print(f"❌ Folder not found: {folder}")
            continue

        # Go through each .json file in the folder
        try:
            filenames = os.listdir(folder)
        except Exception as e:
            print(f"❌ Could not list contents of {folder}: {e}")
            continue
        for filename in filenames:
            # Skip system files like .DS_Store, and hidden files
            if filename.startswith(".") or filename == ".DS_Store":
                continue
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
                    print(f"⚠️ Failed to load {filepath}: {e}")

        # Save the combined output
        with open(output_file, "w") as f:
            json.dump(all_data, f, indent=2)

        print(f"✅ Merged {len(all_data)} entries from '{folder}' into '{output_file}'")


if __name__ == "__main__":
    main()

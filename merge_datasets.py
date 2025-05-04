import json
import os


def load_vignette_dataset(file_path):
    """Load the vignette instruction dataset."""
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"Loaded {len(data)} entries from vignette dataset")
    return data


def load_medical_diagnostic_dataset(file_path):
    """Load the medical diagnostic dataset from JSONL."""
    data = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    print(f"Loaded {len(data)} entries from medical diagnostic dataset")
    return data


def format_diagnostic_entry(entry):
    """Format a diagnostic entry to match the instruction format."""
    # Create a comprehensive instruction
    instruction = "You are a medical assistant. Based on the patient's symptoms, determine the correct diagnosis."

    # Combine the case information with the patient statement
    input_text = f"Case information: {entry['input']}\n\nPatient states: {entry['patient_statement']}"

    # Create output that includes the diagnosis
    output_text = f"Based on the symptoms and medical history, the diagnosis is {entry['target_diagnosis']}."

    return {"instruction": instruction, "input": input_text, "output": output_text}


def merge_datasets(vignette_data, diagnostic_data):
    """Merge the two datasets into a unified format."""
    combined_data = []

    # Add vignette data (already in correct format)
    for entry in vignette_data:
        if "instruction" in entry and "input" in entry and "output" in entry:
            combined_data.append(entry)

    # Convert and add diagnostic data
    for entry in diagnostic_data:
        formatted_entry = format_diagnostic_entry(entry)
        combined_data.append(formatted_entry)

    print(f"Created combined dataset with {len(combined_data)} entries")
    return combined_data


def main():
    vignette_path = "/Users/owner/Downloads/coding projects/AMIE-app/datasets/vignette_instruction_dataset.json"
    diagnostic_path = "/Users/owner/Downloads/coding projects/AMIE-app/datasets/medical_blind_diagnostic_format.jsonl"
    output_path = "/Users/owner/Downloads/coding projects/AMIE-app/datasets/combined_sft_dataset.json"

    vignette_data = load_vignette_dataset(vignette_path)
    diagnostic_data = load_medical_diagnostic_dataset(diagnostic_path)

    combined_data = merge_datasets(vignette_data, diagnostic_data)

    # Save the combined dataset
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(combined_data, f, indent=2)

    print(f"Saved combined dataset to {output_path}")


if __name__ == "__main__":
    main()

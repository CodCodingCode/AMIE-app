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


def load_full_dataset(file_path):
    """Load the full dataset with Q&A format."""
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"Loaded {len(data)} entries from full dataset")
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


def format_medical_entry(entry):
    """Format a medical diagnostic entry to match the instruction format."""
    # Already in the right format, just return as is
    return {
        "instruction": entry["instruction"],
        "input": entry["input"],
        "output": entry["target_diagnosis"]
    }


def format_full_dataset_entry(entry):
    """Format a Q&A style entry to match the instruction format."""
    return {
        "instruction": entry["instruction"],
        "input": entry["input"],
        "output": entry["output"]
    }


def merge_datasets(medical_data, full_data):
    """Merge the two datasets into a unified format."""
    combined_data = []

    # Add medical diagnostic data
    for entry in medical_data:
        formatted_entry = format_medical_entry(entry)
        combined_data.append(formatted_entry)

    # Add full dataset data
    for entry in full_data:
        formatted_entry = format_full_dataset_entry(entry)
        combined_data.append(formatted_entry)

    print(f"Created combined dataset with {len(combined_data)} entries")
    return combined_data


def main():
    medical_path = "/Users/owner/Downloads/coding projects/AMIE-app/datasets/medical_blind_diagnostic_format.jsonl"
    full_dataset_path = "/Users/owner/Downloads/coding projects/AMIE-app/datasets/full_dataset.json"
    output_path = "/Users/owner/Downloads/coding projects/AMIE-app/datasets/combined_sft_dataset.json"

    medical_data = load_medical_diagnostic_dataset(medical_path)
    full_data = load_full_dataset(full_dataset_path)

    combined_data = merge_datasets(medical_data, full_data)

    # Save the combined dataset
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(combined_data, f, indent=2)

    print(f"Saved combined dataset to {output_path}")


if __name__ == "__main__":
    main()

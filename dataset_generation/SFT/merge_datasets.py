import json
import os

# Input folder containing all JSON files
input_folder = "/Users/owner/Downloads/coding projects/AMIE-app/datasets/SFT"

# Output JSONL file path
output_jsonl_path = (
    "/Users/owner/Downloads/coding projects/AMIE-app/datasets/combined_dataset.jsonl"
)


def load_json_file(file_path):
    """Load a JSON or JSONL file and return its data."""
    data = []
    with open(file_path, "r", encoding="utf-8") as f:
        if file_path.endswith(".jsonl"):
            for line in f:
                if line.strip():
                    data.append(json.loads(line))
        elif file_path.endswith(".json"):
            data = json.load(f)
    print(f"Loaded {len(data)} entries from {file_path}")
    return data


def format_entry(entry):
    """Ensure each entry has the required 'instruction', 'input', and 'output' fields."""
    # Default values for missing fields
    instruction = entry.get("instruction", "")
    input_text = entry.get("input", "")
    output_text = entry.get("output", "")

    # Return the formatted entry
    return {
        "instruction": instruction,
        "input": input_text,
        "output": output_text,
    }


def merge_datasets(input_folder, output_jsonl_path):
    """Merge all JSON and JSONL files in the input folder into a single JSONL file."""
    combined_data = []

    # Iterate through all files in the input folder
    for file_name in os.listdir(input_folder):
        file_path = os.path.join(input_folder, file_name)

        # Skip non-JSON/JSONL files
        if not (file_name.endswith(".json") or file_name.endswith(".jsonl")):
            print(f"Skipping non-JSON file: {file_name}")
            continue

        # Load the data from the file
        data = load_json_file(file_path)

        # Format and add each entry to the combined dataset
        for entry in data:
            formatted_entry = format_entry(entry)
            combined_data.append(formatted_entry)

    # Write the combined data to a JSONL file
    with open(output_jsonl_path, "w", encoding="utf-8") as f:
        for entry in combined_data:
            f.write(json.dumps(entry) + "\n")

    print(
        f"Combined dataset saved to {output_jsonl_path} with {len(combined_data)} entries"
    )


if __name__ == "__main__":
    merge_datasets(input_folder, output_jsonl_path)

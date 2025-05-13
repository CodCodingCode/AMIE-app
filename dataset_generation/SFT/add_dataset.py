import json
import os

# File paths
combined_dataset_path = (
    "/Users/owner/Downloads/coding projects/AMIE-app/datasets/combined_dataset.jsonl"
)
new_dataset_path = (
    "/Users/owner/Downloads/coding projects/AMIE-app/datasets/new_dataset.jsonl"
)


def append_to_combined_dataset(combined_path, new_path):
    """
    Append a new dataset to the combined dataset.

    Args:
        combined_path (str): Path to the combined dataset JSONL file.
        new_path (str): Path to the new dataset JSONL file.
    """
    # Load the combined dataset
    combined_data = []
    if os.path.exists(combined_path):
        with open(combined_path, "r", encoding="utf-8") as f:
            combined_data = [json.loads(line) for line in f if line.strip()]
    else:
        print(f"Combined dataset not found at {combined_path}. Creating a new one.")

    # Load the new dataset
    with open(new_path, "r", encoding="utf-8") as f:
        new_data = [json.loads(line) for line in f if line.strip()]

    # Ensure the new data is a list of dictionaries
    if not all(isinstance(entry, dict) for entry in new_data):
        raise ValueError("The new dataset must be a JSONL file with one JSON object per line.")

    # Append the new data to the combined dataset
    combined_data.extend(new_data)

    # Save the updated combined dataset
    with open(combined_path, "w", encoding="utf-8") as f:
        for entry in combined_data:
            f.write(json.dumps(entry) + "\n")

    print(f"Successfully appended {len(new_data)} entries to the combined dataset.")
    print(f"Total entries in the combined dataset: {len(combined_data)}")


# Run the function
append_to_combined_dataset(combined_dataset_path, new_dataset_path)


from datasets import load_dataset
import json

# Load the dataset
dataset = load_dataset("AGBonnet/augmented-clinical-notes")

# Convert to list of dictionaries (assuming 'train' split is needed)
data_list = dataset["train"].to_list()

# Save to JSON
with open("augmented_clinical_notes.json", "w") as f:
    json.dump(data_list, f, indent=2)
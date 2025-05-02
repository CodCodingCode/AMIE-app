import os
import json
import pandas as pd
from datasets import Dataset, DatasetDict


def prepare_csv_dataset(input_file, output_dir="medical_dataset"):
    """
    Prepare the medical diagnostic CSV dataset for training.

    Args:
        input_file: Path to the CSV file
        output_dir: Directory where the processed dataset will be saved
    """
    # Read the CSV file
    df = pd.read_csv(input_file)

    # Create formatted examples for training - with explicit text field
    formatted_data = []
    for _, row in df.iterrows():
        # Format as a complete text field
        formatted_item = {
            "text": f"<s>[INST] Medical diagnosis for: Case vignette: {row['case_vignette']} [/INST] {row['response']}</s>"
        }
        formatted_data.append(formatted_item)

    # Create and save the dataset
    dataset = Dataset.from_list(formatted_data)
    os.makedirs(output_dir, exist_ok=True)

    # Split into train and validation sets (90/10 split)
    dataset_dict = dataset.train_test_split(test_size=0.1)

    # Create a DatasetDict
    final_dataset = DatasetDict(
        {"train": dataset_dict["train"], "validation": dataset_dict["test"]}
    )

    # Save to disk
    final_dataset.save_to_disk(output_dir)

    print(f"Dataset prepared and saved to {output_dir}")
    print(f"Total examples: {len(dataset)}")
    print(f"Training examples: {len(dataset_dict['train'])}")
    print(f"Validation examples: {len(dataset_dict['test'])}")

    return final_dataset


if __name__ == "__main__":
    # Path to your CSV file
    csv_file = "/Users/owner/Downloads/coding projects/AMIE-app/datasets/prompts_gpto1mini_0912_toshare.csv"
    prepare_csv_dataset(csv_file)

from datasets import load_dataset, Dataset
import pandas as pd
from huggingface_hub import HfApi, login

# OPTIONAL: log in to Hugging Face
# login(token="your_huggingface_token")

# Load the full dataset
raw_dataset = load_dataset("CodCodingCode/clinical-conversations", split="train")

# Remove unwanted examples
unwanted_instruction = (
    "You are simulating a real patient in conversation with their doctor."
)
filtered_dataset = raw_dataset.filter(
    lambda row: row["instruction"].strip() != unwanted_instruction
)


# Define formatting check
def has_proper_format(row):
    output = row["output"].strip()
    has_thinking = "THINKING:" in output
    has_answer = "ANSWER:" in output
    correct_order = (
        output.find("THINKING:") < output.find("ANSWER:")
        if has_thinking and has_answer
        else False
    )
    return has_thinking and has_answer and correct_order


# Mark which rows are well-formatted
formatted_dataset = filtered_dataset.map(
    lambda row: {"has_correct_format": has_proper_format(row)}
)

# Convert to pandas and keep only good rows
df_formatted = formatted_dataset.to_pandas()
df_cleaned = df_formatted[df_formatted["has_correct_format"] == True].drop(
    columns=["has_correct_format"]
)

# Convert back to HF dataset
cleaned_hf_dataset = Dataset.from_pandas(df_cleaned)

# Upload only good examples
cleaned_hf_dataset.push_to_hub("CodCodingCode/cleaned-clinical-conversations")

# Confirm
print(f"✅ Uploaded {len(df_cleaned)} properly formatted examples to Hugging Face.")

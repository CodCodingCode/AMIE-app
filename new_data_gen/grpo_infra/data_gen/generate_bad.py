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


# Add the format check flag
formatted_dataset = filtered_dataset.map(
    lambda row: {"has_correct_format": has_proper_format(row)}
)

# Convert to pandas and isolate the bad examples
df_formatted = formatted_dataset.to_pandas()
df_bad = df_formatted[df_formatted["has_correct_format"] == False].drop(
    columns=["has_correct_format"]
)

# Convert bad examples back to Hugging Face Dataset format
bad_hf_dataset = Dataset.from_pandas(df_bad)

# Upload to the Hub (optional: change name)
bad_hf_dataset.push_to_hub("CodCodingCode/misformatted-clinical-conversations")

# Confirm
print(f"❗ Uploaded {len(df_bad)} misformatted examples to Hugging Face.")

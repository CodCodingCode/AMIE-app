from datasets import load_dataset
import pandas as pd

# Load the dataset
dataset = load_dataset("CodCodingCode/clinical-conversations", split="train")

# 1. Remove unwanted instruction
unwanted = "You are simulating a real patient in conversation with their doctor."
filtered = dataset.filter(lambda row: row["instruction"].strip() != unwanted)


# 2. Define checker for THINKING/ANSWER formatting
def has_valid_format(row):
    output = row["output"].strip()
    has_thinking = "THINKING:" in output
    has_answer = "ANSWER:" in output
    correct_order = (
        output.find("THINKING:") < output.find("ANSWER:")
        if has_thinking and has_answer
        else False
    )
    return has_thinking and has_answer and correct_order


# 3. Keep only properly formatted examples
cleaned = filtered.filter(lambda row: has_valid_format(row))

# 4. Save as CSV for future SFT/GRPO
df_cleaned = cleaned.to_pandas()
df_cleaned.to_csv("cleaned_clinical_conversations.csv", index=False)

# (Optional) Show a few rows
print("Total rows after cleaning:", len(df_cleaned))
print(df_cleaned.head(3))

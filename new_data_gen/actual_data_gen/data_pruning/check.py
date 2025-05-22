from datasets import load_dataset
import pandas as pd

# 1. Load the dataset (this will download it under the hood)
dataset = load_dataset("OnDeviceMedNotes/healthbench")

# 2. Inspect available splits
print(dataset)

# 3. Convert one split (e.g. "train") to a pandas DataFrame
df = pd.DataFrame(dataset["test"])

# 4. Show the first 5 rows
print(df.head())

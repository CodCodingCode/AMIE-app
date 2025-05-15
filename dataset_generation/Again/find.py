import pandas as pd
import os
import kagglehub

# Download the dataset
path = kagglehub.dataset_download("dhivyeshrk/diseases-and-symptoms-dataset")

# Locate CSV
csv_files = [f for f in os.listdir(path) if f.endswith(".csv")]
dataset_path = os.path.join(path, csv_files[0])

# Load the dataset
df = pd.read_csv(dataset_path)

# Flatten all cells into a Series and get unique values
all_values = pd.Series(df.values.ravel()).dropna().astype(str)
unique_values = all_values.drop_duplicates().reset_index(drop=True)

# Find the index (position) of the exact match "open wound of the mouth"
target = "open wound of the mouth"
match_index = unique_values[unique_values.str.lower() == target.lower()].index

# Output result
if not match_index.empty:
    print(f'"{target}" found at unique value index: {match_index[0]}')
else:
    print(f'"{target}" not found in the dataset.')

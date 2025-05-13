import pandas as pd

# Load the metadata and dialogue datasets
meta_df = pd.read_csv(
    "dataset_generation/datasets_for_dataGen/aci-bench/challenge_data_json/challenge_data/clef_taskC_test3_metadata.csv"
)
dialogue_df = pd.read_csv(
    "dataset_generation/datasets_for_dataGen/aci-bench/challenge_data_json/challenge_data/clef_taskC_test3.csv"
)

# Merge the two datasets on shared keys
merged_df = pd.merge(meta_df, dialogue_df, on=["dataset", "encounter_id"])
merged_df.to_csv(
    "dataset_generation/datasets_for_dataGen//clef_taskC_test3_merged.csv", index=False
)

# Preview the merged result
print(merged_df.head())

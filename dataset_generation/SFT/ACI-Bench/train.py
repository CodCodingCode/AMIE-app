import pandas as pd

# Load the metadata and dialogue datasets
meta_df = pd.read_csv(
    "/Users/owner/Downloads/coding projects/AMIE-app/dataset_generation/datasets_for_dataGen/aci-bench/src_experiment_data/valid_virtscribe_humantrans_metadata.csv"
)
dialogue_df = pd.read_csv(
    "/Users/owner/Downloads/coding projects/AMIE-app/dataset_generation/datasets_for_dataGen/aci-bench/src_experiment_data/valid_virtscribe_humantrans.csv"
)

# Merge the two datasets on shared keys
merged_df = pd.merge(meta_df, dialogue_df, on=["dataset", "id"])
merged_df.to_csv("clef_taskC_test3_merged21.csv", index=False)

# Preview the merged result
print(merged_df.head())

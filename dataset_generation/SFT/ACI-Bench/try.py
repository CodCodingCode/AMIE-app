import os
import pandas as pd

# Setup
folder = (
    "/Users/owner/Downloads/coding projects/AMIE-app/dataset_generation/SFT/ACI-Bench"
)
filename_prefix = "clef_taskC_test3_merged"
merged_dfs = []

# Load all matching files
for i in range(2, 21):
    file_path = os.path.join(folder, f"{filename_prefix}{i}.csv")
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)

        # Drop 'id' if it's the same as 'encounter_id'
        if "id" in df.columns and "encounter_id" in df.columns:
            if df["id"].equals(df["encounter_id"]):
                df = df.drop(columns=["id"])

        # Add source tag
        df["source_version"] = i
        merged_dfs.append(df)
        print(f"✅ Loaded: {file_path}")
    else:
        print(f"❌ Not found: {file_path}")

# Combine and save
if merged_dfs:
    merged_df = pd.concat(merged_dfs, ignore_index=True)
    output_path = os.path.join(folder, f"{filename_prefix}_all.csv")
    merged_df.to_csv(output_path, index=False)
    print(f"\n✅ All files merged and saved to: {output_path}")
else:
    print("\n⚠️ No files matched the pattern.")


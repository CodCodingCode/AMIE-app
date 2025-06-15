import pandas as pd
import os

def filter_common_diseases(input_file, output_file):
    """
    Filters a CSV file to keep only rows where 'verified_classification'
    contains 'common disease'.
    """
    try:
        df = pd.read_csv(input_file)
    except FileNotFoundError:
        print(f"Error: Input file not found at {input_file}")
        return

    # Filter rows where 'verified_classification' contains 'common disease'
    common_diseases_df = df[df['verified_classification'].str.contains("common disease", na=False)]

    # Save to new file
    common_diseases_df.to_csv(output_file, index=False)

    print(f"Original: {len(df)} entries")
    print(f"Filtered (common diseases): {len(common_diseases_df)} entries")
    print(f"Saved to: {output_file}")

if __name__ == "__main__":
    # The script is in searchstuff/new_icd, and the csv files are in the same directory
    script_dir = os.path.dirname(__file__)
    input_csv = os.path.join(script_dir, "disease_verification_results.csv")
    output_csv = os.path.join(script_dir, "common_diseases.csv")
    filter_common_diseases(input_csv, output_csv)

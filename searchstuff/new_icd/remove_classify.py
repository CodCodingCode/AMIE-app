import pandas as pd

def remove_unclassified_entries(input_file, output_file):
    """
    Remove rows with blank classifications and save to new CSV.
    """
    df = pd.read_csv(input_file)
    
    # Keep only rows with non-empty classifications
    classified_df = df[df['classification'].notna() & (df['classification'] != '')]
    
    # Save to new file
    classified_df.to_csv(output_file, index=False)
    
    print(f"Original: {len(df)} entries")
    print(f"Classified: {len(classified_df)} entries")
    print(f"Removed: {len(df) - len(classified_df)} entries")
    print(f"Saved to: {output_file}")

if __name__ == "__main__":
    # Usage
    remove_unclassified_entries("manual1_classified.csv", "manual1_clean.csv")
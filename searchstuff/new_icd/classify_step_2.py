import pandas as pd

def extract_unclassified_entries(input_file, unclassified_output, classified_output):
    """
    Extract rows with blank classifications into a separate CSV file and remove them from original.
    """
    df = pd.read_csv(input_file)
    
    # Find rows with blank/empty classifications
    blank_mask = df['classification'].isna() | (df['classification'] == '')
    
    unclassified_entries = df[blank_mask]
    classified_entries = df[~blank_mask]
    
    # Save both files
    unclassified_entries.to_csv(unclassified_output, index=False)
    classified_entries.to_csv(classified_output, index=False)
    
    print(f"Total entries: {len(df)}")
    print(f"Unclassified entries: {len(unclassified_entries)} -> {unclassified_output}")
    print(f"Classified entries: {len(classified_entries)} -> {classified_output}")

if __name__ == "__main__":
    # Usage
    extract_unclassified_entries("common_diseases_live_updates.csv", "unclassified_entries.csv", "manual1_clean.csv")
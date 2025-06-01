import pandas as pd
import os

def cleanup_csv():
    """Clean up the corrupted CSV file"""
    csv_path = "realdatasets/classified_diseases_live2.csv"
    
    if not os.path.exists(csv_path):
        print("CSV file not found")
        return
    
    # Read the CSV
    df = pd.read_csv(csv_path)
    original_count = len(df)
    print(f"Original records: {original_count}")
    
    # Remove corrupted records where Title contains comma
    # This indicates malformed data like "Gartner duct,NotLevator anguli oris tendon"
    clean_df = df[~df['Title'].str.contains(',', na=False)]
    clean_count = len(clean_df)
    
    print(f"Clean records: {clean_count}")
    print(f"Removed {original_count - clean_count} corrupted records")
    
    # Check for any other anomalies
    print(f"Unique categories: {clean_df['Category'].value_counts()}")
    
    # Save the cleaned version
    clean_df.to_csv(csv_path, index=False)
    print(f"Cleaned CSV saved to {csv_path}")

if __name__ == "__main__":
    cleanup_csv() 
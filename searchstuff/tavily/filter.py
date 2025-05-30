import pandas as pd

def filter_diseases(input_csv: str, output_csv: str):
    """
    Filter diseases from the input CSV and save to a new CSV file without duplicates.
    
    Args:
        input_csv (str): Path to the input CSV file.
        output_csv (str): Path to the output CSV file.
    """
    try:
        # Read the input CSV file
        df = pd.read_csv(input_csv)

        # Filter rows where the 'term' column contains '(disorder)'
        filtered_df = df[df['term'].str.contains(r'\(disorder\)', na=False, case=False)]

        # Remove duplicate rows based on all columns
        filtered_df = filtered_df.drop_duplicates(subset=['term'])

        # Save the filtered DataFrame to a new CSV file
        filtered_df.to_csv(output_csv, index=False)

        print(f"Filtered diseases saved to {output_csv} (duplicates removed)")

    except Exception as e:
        print(f"An error occurred: {e}")

# Usage
input_file = 'output.csv'
output_file = 'filtered_diseases.csv'
filter_diseases(input_file, output_file)

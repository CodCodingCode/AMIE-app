import json
import csv

def convert_json_to_csv(json_file_path, csv_file_path):
    """
    Converts a JSON file with disease verification results to a CSV file.

    The CSV file will contain two columns: 'disease' and 'verified_classification'.
    """
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    results = data.get('results', [])

    with open(csv_file_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Write header
        writer.writerow(['disease', 'verified_classification'])
        
        # Write data
        for result in results:
            disease = result.get('disease')
            verified_classification = result.get('verified_classification')
            if disease and verified_classification:
                writer.writerow([disease, verified_classification])

    print(f"Successfully converted {json_file_path} to {csv_file_path}")

if __name__ == '__main__':
    input_json = 'disease_verification_results_detailed.json'
    output_csv = 'disease_verification_results.csv'
    convert_json_to_csv(input_json, output_csv)


import json
import csv
import os

def convert_json_to_csv(json_file_path, csv_file_path):
    """
    Parses a JSON file containing disease data, extracts disease names,
    and writes them to a CSV file.

    Args:
        json_file_path (str): The path to the input JSON file.
        csv_file_path (str): The path to the output CSV file.
    """
    try:
        # Step 1: Open and parse the JSON file
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Step 2: Extract the list of nodes which contain the disease info
        nodes = data.get('graphs', [{}])[0].get('nodes', [])
        
        if not nodes:
            print("No disease nodes found in the JSON data.")
            return

        # Step 3: Open the specified CSV file in write mode
        with open(csv_file_path, mode='w', newline='', encoding='utf-8') as csv_file:
            # Step 4: Create a CSV writer object
            fieldnames = ['disease']
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

            # Step 5: Write the header row to the CSV
            writer.writeheader()

            # Step 6: Iterate through each node and write the disease label to the CSV
            for node in nodes:
                # The disease name is in the 'lbl' key
                disease_name = node.get('lbl')
                if disease_name:
                    writer.writerow({'disease': disease_name})
        
        print(f"Successfully converted data from '{json_file_path}' to '{csv_file_path}'")

    except FileNotFoundError:
        print(f"Error: Input file not found at '{json_file_path}'")
    except json.JSONDecodeError:
        print("Error: Invalid JSON format.")
    except (KeyError, IndexError) as e:
        print(f"Error: Could not find the expected data structure in the JSON. Missing key: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


# --- Main execution ---
if __name__ == "__main__":
    # Get the directory where the script is located
    script_dir = os.path.dirname(__file__)
    
    # Define the input JSON file and output CSV file paths
    input_json_file = os.path.join(script_dir, 'doid.json')
    output_csv_file = os.path.join(script_dir, 'diseases.csv')
    
    # Call the function to perform the conversion
    convert_json_to_csv(input_json_file, output_csv_file)

    # Optionally print the first 10 lines of the generated file
    print(f"\n--- Contents of {output_csv_file} (first 10 lines) ---")
    try:
        with open(output_csv_file, 'r') as f:
            for i, line in enumerate(f):
                if i >= 11:  # header + 10 lines
                    break
                print(line, end='')
    except FileNotFoundError:
        print(f"Could not find the output file to print.")
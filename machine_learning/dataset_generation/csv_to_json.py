import csv
import json
import os
import ast  # To safely parse strings that look like Python lists/dicts

# Input CSV file path
input_csv_path = "/Users/owner/Downloads/coding projects/AMIE-app/datasets/prompts_gpto1preview_0912_toshare.csv"

# Output JSON file path
output_json_path = "/Users/owner/Downloads/coding projects/AMIE-app/datasets/prompts_gpto1mini_0912_toshare.json"


def clean_text_field(field):
    """
    Extract plain text from a field containing structured data like [{'role': 'user', 'content': '...'}].
    """
    try:
        # Parse the string into a Python list/dict
        parsed_field = ast.literal_eval(field)
        if isinstance(parsed_field, list):
            # Extract 'content' from each dictionary in the list
            return " ".join(
                [
                    entry.get("content", "")
                    for entry in parsed_field
                    if isinstance(entry, dict)
                ]
            )
        elif isinstance(parsed_field, dict):
            # If it's a single dictionary, return its 'content'
            return parsed_field.get("content", "")
    except (ValueError, SyntaxError):
        # If parsing fails, return the original field
        return field


def csv_to_json(input_csv, output_json):
    data_list = []

    # Read the CSV file
    with open(input_csv, mode="r", encoding="utf-8") as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for row in csv_reader:
            # Clean the instruction and output fields
            cleaned_instruction = clean_text_field(row["instruction"])
            cleaned_output = clean_text_field(row["response"])

            # Construct the JSON object for each row
            json_object = {
                "instruction": cleaned_instruction,
                "input": row["case_vignette"],
                "output": cleaned_output,
            }
            data_list.append(json_object)

    # Write the JSON data to a file
    with open(output_json, mode="w", encoding="utf-8") as json_file:
        json.dump(data_list, json_file, indent=4)

    print(f"JSON file has been created at: {os.path.abspath(output_json)}")


# Run the conversion
csv_to_json(input_csv_path, output_json_path)

import json


def convert_json_to_jsonl(input_json_path, output_jsonl_path):
    """
    Converts a JSON file containing a list of objects to a JSONL file.

    Args:
        input_json_path (str): Path to the input JSON file.
        output_jsonl_path (str): Path to the output JSONL file.
    """
    try:
        with open(input_json_path, "r", encoding="utf-8") as infile, open(
            output_jsonl_path, "w", encoding="utf-8"
        ) as outfile:

            # Load the entire JSON list from the input file
            data = json.load(infile)

            # Check if the loaded data is a list
            if not isinstance(data, list):
                print(
                    f"Error: Input JSON file '{input_json_path}' does not contain a list."
                )
                return

            # Iterate through each object in the list
            for item in data:
                # Convert the Python dictionary back to a JSON string
                json_line = json.dumps(item, ensure_ascii=False)
                # Write the JSON string as a new line in the output file
                outfile.write(json_line + "\n")

        print(f"Successfully converted '{input_json_path}' to '{output_jsonl_path}'")

    except FileNotFoundError:
        print(f"Error: Input file not found at '{input_json_path}'")
    except json.JSONDecodeError:
        print(
            f"Error: Could not decode JSON from '{input_json_path}'. Check file format."
        )
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


# --- Configuration ---
input_file = (
    "/Users/owner/Downloads/coding projects/AMIE-app/datasets/combined_sft_dataset.json"
)
output_file = "/Users/owner/Downloads/coding projects/AMIE-app/datasets/combined_sft_dataset.jsonl"

# --- Run Conversion ---
if __name__ == "__main__":
    convert_json_to_jsonl(input_file, output_file)

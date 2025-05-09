import json


def split_json_file(input_file, output_file1, output_file2):
    """
    Split a JSON file into two halves and save them as separate files.

    Args:
        input_file (str): Path to the input JSON file.
        output_file1 (str): Path to the first output JSON file.
        output_file2 (str): Path to the second output JSON file.
    """
    try:
        # Load the JSON file
        with open(input_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Ensure the data is a list
        if not isinstance(data, list):
            print("Error: The JSON file does not contain a list.")
            return

        # Split the list into two halves
        mid_index = len(data) // 2
        part1 = data[:mid_index]
        part2 = data[mid_index:]

        # Save each half to a separate file
        with open(output_file1, "w", encoding="utf-8") as f1:
            json.dump(part1, f1, indent=4)
        with open(output_file2, "w", encoding="utf-8") as f2:
            json.dump(part2, f2, indent=4)

        print(
            f"Successfully split the JSON file into {output_file1} and {output_file2}."
        )

    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error processing the JSON file: {e}")


# Example usage
input_file = "malacards-diseases.json"
output_file1 = "malacard-diseases-part1.json"
output_file2 = "malacard-diseases-part2.json"

split_json_file(input_file, output_file1, output_file2)

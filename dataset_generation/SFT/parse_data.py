import json

# File paths
input_file_path = (
    "/Users/owner/Downloads/coding projects/AMIE-app/datasets/iCliniq.json"
)
output_files = {
    "answer_icliniq": "/Users/owner/Downloads/coding projects/AMIE-app/datasets/answer_icliniq.json",
    "answer_chatgpt": "/Users/owner/Downloads/coding projects/AMIE-app/datasets/answer_chatgpt.json",
    "answer_chatdoctor": "/Users/owner/Downloads/coding projects/AMIE-app/datasets/answer_chatdoctor.json",
}


def create_instruction_input_output_files(input_path, output_paths):
    """
    Create three JSON files formatted with instruction, input, and output fields.

    Args:
        input_path (str): Path to the input JSON file.
        output_paths (dict): Dictionary with keys as response types and values as output file paths.
    """
    # Load the input JSON file
    try:
        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error loading input file: {e}")
        return

    # Initialize dictionaries for each output file
    formatted_data = {key: [] for key in output_paths.keys()}

    # Process each entry in the input data
    for idx, entry in enumerate(data):
        instruction = entry.get("input", "").strip()
        if not instruction:
            print(f"Skipping entry {idx}: Missing 'input' field.")
            continue

        for key in output_paths.keys():
            # Use the correct key names from the dataset
            output = entry.get(key, "").strip()
            if not output:
                print(f"Skipping entry {idx}: Missing '{key}' field.")
                continue

            formatted_data[key].append(
                {"instruction": instruction, "input": "", "output": output}
            )

    # Write to the respective output files
    for key, file_path in output_paths.items():
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(formatted_data[key], f, indent=4)
            print(f"File created: {file_path} with {len(formatted_data[key])} entries.")
        except Exception as e:
            print(f"Error writing to file {file_path}: {e}")


# Run the function
create_instruction_input_output_files(input_file_path, output_files)
import json


def transform_prompts(input_file_path, output_file_path):
    """
    Reads a JSON file, filters and transforms its content,
    and writes the result to a new JSON file.

    Args:
        input_file_path (str): Path to the input JSON file.
        output_file_path (str): Path to the output JSON file.
    """
    transformed_data = []
    try:
        with open(input_file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        for item in data:
            if (
                "output" in item
                and isinstance(item["output"], str)
                and "**Final Diagnosis:**" not in item["output"]
            ):
                new_item = {
                    "instruction": item.get("instruction", ""),
                    "input": item["output"],
                }
                transformed_data.append(new_item)

        with open(output_file_path, "w", encoding="utf-8") as f:
            json.dump(transformed_data, f, indent=4)

        print(f"Successfully transformed data and saved to {output_file_path}")

    except FileNotFoundError:
        print(f"Error: Input file not found at {input_file_path}")
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {input_file_path}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")



if __name__ == "__main__":
    input_json_path = "datasets/prompts_gpto1mini_0912_toshare.json"
    output_json_path = "machine_learning/dataset_generation/transformed_prompts.json"  # Output will be in the same directory as the script

    transform_prompts(input_json_path, output_json_path)

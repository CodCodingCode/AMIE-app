import json
import os


def convert_sft_to_openai_format(input_jsonl_path, output_jsonl_path):
    """
    Converts an SFT dataset (instruction, input, output) in JSONL format
    to the OpenAI fine-tuning format with a 'messages' key.

    Args:
        input_jsonl_path (str): Path to the input SFT JSONL file.
        output_jsonl_path (str): Path to the output OpenAI format JSONL file.
    """
    try:
        # Ensure the output directory exists
        os.makedirs(os.path.dirname(output_jsonl_path), exist_ok=True)

        with open(input_jsonl_path, "r", encoding="utf-8") as infile, open(
            output_jsonl_path, "w", encoding="utf-8"
        ) as outfile:

            count = 0
            for line in infile:
                try:
                    # Load the JSON object from the line
                    sft_entry = json.loads(line.strip())

                    # Extract instruction, input, and output
                    instruction = sft_entry.get("instruction", "")
                    input_text = sft_entry.get("input", "")
                    output_text = sft_entry.get("output", "")

                    # Validate that required fields are present
                    if not instruction or not input_text or not output_text:
                        print(
                            f"Warning: Skipping line {count + 1} due to missing fields: {line.strip()}"
                        )
                        continue

                    # Construct the messages list for OpenAI format
                    messages = []
                    # Use instruction as the system message
                    messages.append({"role": "system", "content": instruction})
                    # Use input as the user message
                    messages.append({"role": "user", "content": input_text})
                    # Use output as the assistant message
                    messages.append({"role": "assistant", "content": output_text})

                    # Create the final JSON object for the line
                    openai_entry = {"messages": messages}

                    # Convert the Python dictionary back to a JSON string
                    json_line = json.dumps(openai_entry, ensure_ascii=False)
                    # Write the JSON string as a new line in the output file
                    outfile.write(json_line + "\n")
                    count += 1

                except json.JSONDecodeError:
                    print(f"Warning: Skipping invalid JSON line: {line.strip()}")
                except Exception as e:
                    print(
                        f"Warning: Skipping line due to error: {e} - Line: {line.strip()}"
                    )

        print(
            f"Successfully converted {count} entries from '{input_jsonl_path}' to '{output_jsonl_path}'"
        )

    except FileNotFoundError:
        print(f"Error: Input file not found at '{input_jsonl_path}'")
    except Exception as e:
        print(f"An unexpected error occurred during conversion: {e}")


# --- Configuration ---
input_file = "datasets/combined_sft_dataset.jsonl"
output_file = "datasets/openai_finetune_format.jsonl"

# --- Run Conversion ---
if __name__ == "__main__":
    convert_sft_to_openai_format(input_file, output_file)
import json
import os


def clean_output(text):
    # Strip wrapping quotes like "\"example\""
    if text.startswith('"') and text.endswith('"'):
        text = text[1:-1]

    # Replace escaped quotes with normal quotes
    return text.replace('\\"', '"').strip()


def convert_case_to_instruction(case):
    return {
        "instruction": (
            "You are a patient. Based off of the doctors questions, please respond accordingly."
        ),
        "input": (f"{case['doctor_vignette']}\n\n"),
        "output": clean_output(case["ruling_out_question"]),
    }


def convert_file(input_path, output_path):
    with open(input_path, "r") as infile:
        data = json.load(infile)

    converted_data = [convert_case_to_instruction(case) for case in data]

    with open(output_path, "w") as outfile:
        json.dump(converted_data, outfile, indent=2, ensure_ascii=False)

    print(f"✅ Converted {len(data)} cases from {input_path} to {output_path}")


# Example usage
if __name__ == "__main__":
    input_files = ["aci_vignette_qa.jsonl"]
    for fname in input_files:
        output_name = f"converted_{os.path.basename(fname)}"
        convert_file(fname, output_name)

import json
import os


def clean_output(text):
    if text.startswith('"') and text.endswith('"'):
        text = text[1:-1]
    return text.replace('\\"', '"').strip()

def convert_case_to_instruction(case):
    return {
        "instruction": "You are a patient. Based off of the doctors questions, please respond accordingly.",  # Doctor's question becomes instruction
        "input": f"""Doctor Vignette: {clean_output(case["instruction"])}, Question: {clean_output(case["input"])}""",  # Vignette as optional context
        "output": clean_output(case["output"]),  # Patient's response
    }

def convert_file(input_path, output_path):
    with open(input_path, "r") as infile:
        # Read JSONL lines
        data = [json.loads(line) for line in infile]

    converted_data = [convert_case_to_instruction(case) for case in data]

    with open(output_path, "w") as outfile:
        json.dump(converted_data, outfile, indent=2, ensure_ascii=False)

    print(f"✅ Converted {len(data)} cases from {input_path} to {output_path}")


# Example usage
if __name__ == "__main__":
    input_files = ["datasets/SFT/augmented_clinical_notes_qa.jsonl"]
    for fname in input_files:
        output_name = f"converted_{os.path.basename(fname)}"
        convert_file(fname, output_name)

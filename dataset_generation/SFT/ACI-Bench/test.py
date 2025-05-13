import json
import os


def clean_output(text):
    if text.startswith('"') and text.endswith('"'):
        text = text[1:-1]
    return text.replace('\\"', '"').strip()


def convert_case_to_instruction(case):
    return {
        "instruction": (
            "You are a patient. Based off of the doctors questions, please respond accordingly."
        ),
        "input": case["input"],
        "output": clean_output(case["output"]),
    }


def convert_file(input_path, output_path):
    converted_data = []

    with open(input_path, "r", encoding="utf-8") as infile:
        for line in infile:
            case = json.loads(line)
            converted_data.append(convert_case_to_instruction(case))

    with open(output_path, "w", encoding="utf-8") as outfile:
        json.dump(converted_data, outfile, indent=2, ensure_ascii=False)

    print(
        f"✅ Converted {len(converted_data)} cases from {input_path} to {output_path}"
    )



# Example usage
if __name__ == "__main__":
    input_files = ["aci_vignette_qa.jsonl"]
    for fname in input_files:
        output_name = f"converted_{os.path.splitext(os.path.basename(fname))[0]}.json"
        convert_file(fname, output_name)

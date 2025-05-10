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
            "You are a medical expert tasked with creating a counter deductive reasoning question. "
            "Your goal is to formulate a question that would help INCREASE the probability of this disease. "
            "Make your question specific, clinically relevant, and targeted towards increasing the probability of the specified disease."
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
    input_files = ["datasets/SFT/counter_d.json"]
    for fname in input_files:
        output_name = f"converted_{os.path.basename(fname)}"
        convert_file(fname, output_name)

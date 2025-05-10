import json


def add_instruction_to_inputs(input_path, output_path):
    instruction_text = "You are a medical assisstant. Based off of the patient's vignette, generate the best diagnosis of the patient. Do not include any other information or context."

    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    transformed = []
    for item in data:
        if "input" in item:
            transformed.append(
                {"instruction": instruction_text, "input": item["input"]}
            )

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(transformed, f, indent=2)

    print(f"✅ Transformed {len(transformed)} entries and saved to {output_path}")


# Example usage
add_instruction_to_inputs("vignettes_as_input.json", "vignettes_with_instruction.json")
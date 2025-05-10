import json


def add_instruction_wrappers(input_path, output_path):
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    intro = "I am a patient that is currently getting diagnosed.\n"
    outro = "\nPlease respond to the question using the data about yourself."

    for item in data:
        original_instruction = item.get("instruction", "")
        item["instruction"] = f"{intro}{original_instruction}{outro}"

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print(
        f"✅ Instruction updated and saved to {output_path}. {len(data)} records processed."
    )


# Example usage
add_instruction_wrappers(
    "machine_learning/dataset_generation/filtered_questions.json", "final_dataset.json"
)

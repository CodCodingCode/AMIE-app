# This file is for checking the qaulity of the question generation data

import json
import re


def extract_answers_from_json(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    extracted_answers = []
    for entry in data:
        output = entry.get("output", "")
        match = re.search(r"ANSWER:\s*(.*)", output, re.DOTALL)
        if match:
            answer_text = match.group(1).strip()
            extracted_answers.append(
                {"vignette_index": entry.get("vignette_index"), "answer": answer_text}
            )

    return extracted_answers


# Example usage:
answers = extract_answers_from_json("first_train/2questioning_doctor_outputs.json")
for ans in answers:
    print(f"Vignette {ans['vignette_index']} → Answer: {ans['answer']}\n")

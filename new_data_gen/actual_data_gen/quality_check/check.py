# This file is for checking the qaulity of the question generation data

import json
import re

missing_count = 0


def extract_answers_from_json(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    extracted_answers = []
    missing_entries = []

    for entry in data:
        output = entry.get("output", "")
        thinking_match = re.search(r"THINKING:\s*(.*?)(?:ANSWER:|$)", output, re.DOTALL)
        answer_match = re.search(r"ANSWER:\s*(.*)", output, re.DOTALL)

        if thinking_match and answer_match:
            thinking_text = thinking_match.group(1).strip()
            answer_text = answer_match.group(1).strip()
            extracted_answers.append(
                {
                    "vignette_index": entry.get("vignette_index"),
                    "thinking": thinking_text,
                    "answer": answer_text,
                }
            )
        else:
            missing_entries.append(entry.get("vignette_index"))

    print(f"Total entries missing either THINKING or ANSWER: {len(missing_entries)}")
    print("Missing entry indices:", missing_entries)
    return extracted_answers


def split_by_letter(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    split_data = {}
    for entry in data:
        letter = entry.get("letter")
        if letter:
            if letter not in split_data:
                split_data[letter] = []
            split_data[letter].append(entry)

    for letter, entries in split_data.items():
        with open(f"split_outputs_{letter}.json", "w", encoding="utf-8") as f_out:
            json.dump(entries, f_out, indent=2, ensure_ascii=False)


list_of_outputs = [
    "all_diagnosing_doctor_outputs.json",
    "all_questioning_doctor_outputs.json",
    "all_summarizer_outputs.json",
    "all_treatment_outputs.json",
]

for output_file in list_of_outputs:

    answers = extract_answers_from_json(output_file)

# Call the new function to split the dataset
# split_by_letter("all_questioning_doctor_outputs.json")
print("total missing entries:", missing_count)

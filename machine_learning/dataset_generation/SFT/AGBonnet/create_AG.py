import json

# Path to your dataset (replace with your actual file path)
input_json_path = (
    "datasets/SFT/augmented_clinical_notes.json"  # 👈 Replace with your filename
)
output_jsonl_path = "augmented_clinical_notes_qa.jsonl"

# Load the dataset
with open(input_json_path, "r", encoding="utf-8") as f:
    data = json.load(f)

# Extract instruction-input-output triples
qa_pairs = []
for entry in data:
    note = entry.get("note", "").strip()
    conversation = entry.get("conversation", "").strip()
    lines = conversation.split("\n")

    for i in range(len(lines)):
        if (
            lines[i].startswith("Doctor:")
            and i + 1 < len(lines)
            and lines[i + 1].startswith("Patient:")
        ):
            doctor_question = lines[i].replace("Doctor:", "").strip()
            patient_answer = lines[i + 1].replace("Patient:", "").strip()
            qa_pairs.append(
                {
                    "instruction": note,
                    "input": doctor_question,
                    "output": patient_answer,
                }
            )

# Write to JSONL
with open(output_jsonl_path, "w", encoding="utf-8") as f:
    for qa in qa_pairs:
        f.write(json.dumps(qa, ensure_ascii=False) + "\n")

print(f"✅ Saved {len(qa_pairs)} instruction-input-output pairs to {output_jsonl_path}")

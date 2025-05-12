import json

# Path to your input JSON file (change this to your actual file path)
input_path = "datasets/other/dialogs (3).json"  # ← Replace with your file path
output_path = "doctor_oriented_qa_with_ids.jsonl"

# Load data
with open(input_path, "r", encoding="utf-8") as f:
    raw_data = json.load(f)

qa_pairs = []

# Loop through each dialog
for dialog_id, dialog in raw_data.items():
    dlg_id = dialog.get("dlg_id", dialog_id)
    utterances = dialog.get("utterances", [])

    for i in range(len(utterances) - 1):
        current = utterances[i]
        next_ = utterances[i + 1]

        # Doctor → Patient QA only
        if current["speaker"] == "doctor" and next_["speaker"] == "patient":
            qa_pairs.append({
                "id": dlg_id,
                "input": current["text"].strip(),
                "output": next_["text"].strip()
            })

# Save as JSONL
with open(output_path, "w", encoding="utf-8") as f:
    for qa in qa_pairs:
        f.write(json.dumps(qa, ensure_ascii=False) + "\n")

print(f"✅ Saved {len(qa_pairs)} QA pairs to {output_path}")
import json

# Load your file
with open(
    "dataset_generation/datasets_for_dataGen/aci-bench/challenge_data_json/clef_taskC_test3_full.json",
    "r",
) as f:
    data = json.load(f)

qa_data = []

for entry in data["data"]:
    conversation = entry["src"]
    lines = conversation.strip().split("\n")

    # Step through the lines and pair doctor→patient turns
    for i in range(len(lines) - 1):
        if lines[i].startswith("[doctor]") and lines[i + 1].startswith("[patient]"):
            doctor_q = lines[i].replace("[doctor]", "").strip()
            patient_a = lines[i + 1].replace("[patient]", "").strip()

            qa_data.append(
                {
                    "instruction": "You are a patient. Based off of the doctors questions, please respond accordingly.",
                    "input": f"""Patient Vignette: {entry.get("tgt", "").strip()} Question: {doctor_q}""",
                    "output": patient_a,
                }
            )




# Save as JSONL
with open("aci_vignette_qa.jsonl", "w") as out:
    for item in qa_data:
        out.write(json.dumps(item, ensure_ascii=False) + "\n")

print(f"✅ Extracted {len(qa_data)} doctor-patient pairs.")

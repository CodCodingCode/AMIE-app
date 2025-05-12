import json
import time
from collections import defaultdict
from openai import OpenAI  # ✅ NEW SDK format

# Your OpenAI API key
api_key = "sk-..."  # ← Replace with your actual key
Client = OpenAI(api_key=api_key)

# File paths
input_path = "doctor_patient_dialogs.jsonl"  # ← Your JSONL dataset
output_path = "vignette_summaries.jsonl"

# Load input data
with open(input_path, "r", encoding="utf-8") as f:
    lines = [json.loads(line) for line in f]

# Group entries by dialogue ID
dialogs = defaultdict(list)
for entry in lines:
    dialogs[entry["id"]].append(entry)

# Generate summaries turn-by-turn
with open(output_path, "w", encoding="utf-8") as out_file:
    for dlg_id, turns in dialogs.items():
        qa_so_far = []

        for i, turn in enumerate(turns):
            qa_so_far.append({"q": turn["input"], "a": turn["output"]})

            # Build conversation text
            dialogue_text = "\n".join(
                [f"Doctor: {qa['q']}\nPatient: {qa['a']}" for qa in qa_so_far]
            )

            # Prompt to model
            prompt = (
                "You are a clinical assistant. Based on the following dialogue between a doctor and a patient, "
                "summarize the patient's condition so far as a clinical vignette. Use concise medical language.\n\n"
                f"{dialogue_text}\n\nVignette summary:"
            )

            try:
                response = Client.chat.completions.create(
                    model="gpt-4",  # or "gpt-3.5-turbo"
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a medical scribe summarizing patient history.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.4,
                )

                summary = response.choices[0].message.content.strip()

            except Exception as e:
                summary = f"[ERROR] {str(e)}"

            # Save each step's vignette
            out_file.write(
                json.dumps(
                    {
                        "id": dlg_id,
                        "turn": i + 1,
                        "dialog_so_far": qa_so_far.copy(),
                        "summary": summary,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )

            # Respect rate limits
            time.sleep(1.2)

print(f"✅ Done! Summaries saved to {output_path}")

from datasets import load_dataset
import json

# 1) load the HF dataset
ds = load_dataset("GBaker/MedQA-USMLE-4-options", split="train")

# 2) open a JSONL for writing
with open("medqa_usmle_4opt_prompts.jsonl", "w") as fout:
    for ex in ds:
        # --- adjust these to your actual column names ---
        question = ex["question"]  # the stem of the USMLE item
        options_field = ex["options"]  # e.g. a dict {"A": "...", "B": "...", ...}
        correct = ex["answer"]  # e.g. "C" or "D"
        # ----------------------------------------------

        # if HuggingFace stored the options as a JSON‐string, uncomment:
        # if isinstance(options_field, str):
        #     options_field = json.loads(options_field)

        # build the "input" block
        choices_lines = [f"{letter}: {text}" for letter, text in options_field.items()]
        input_block = question + "\n" + "\n".join(choices_lines)

        # emit one JSON per line
        record = {"instruction": "0", "input": input_block, "output": correct}
        fout.write(json.dumps(record, ensure_ascii=False) + "\n")

print("→ Wrote", len(ds), "records to medqa_usmle_4opt_prompts.jsonl")

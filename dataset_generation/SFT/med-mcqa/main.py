from datasets import load_dataset
import json

# 1) Load the HF MedMCQA dataset
ds = load_dataset("openlifescienceai/medmcqa", split="train")

# 2) Conversion function
def to_iii(example):
    # build choices dict
    opts = {
        "A": example["opa"],
        "B": example["opb"],
        "C": example["opc"],
        "D": example["opd"],
    }
    # build input: question + each option on its own line
    choice_lines = [f"{k}: {v}" for k, v in opts.items()]
    input_text   = example["question"] + "\n" + "\n".join(choice_lines)

    # map cop (0-based index) to letter
    # if cop is already 1-based, change the list accordingly
    letter_map = ["A", "B", "C", "D"]
    correct    = letter_map[example["cop"]]

    return {
        "instruction": "0",
        "input":       input_text,
        "output":      correct,
    }

# 3) Apply the mapping (drop all other columns)
iii_ds = ds.map(to_iii, remove_columns=ds.column_names)

# 4) Write out to JSONL
with open("medmcqa_iii.jsonl", "w") as f:
    for rec in iii_ds:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")

print(f"Wrote {len(iii_ds)} records to medmcqa_iii.jsonl")
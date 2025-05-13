import pandas as pd
import json

# 1) Load your combined CSV
df = pd.read_csv("/Users/owner/Downloads/coding projects/AMIE-app/combined.csv")

# 2) Set your instruction text
INSTRUCTION = (
    "You are a medical expert tasked with creating a counter deductive reasoning question. "
    "Your goal is to formulate a question that would help INCREASE the probability of this disease. "
    "Make your question specific, clinically relevant, and targeted towards increasing the probability "
    "of the specified disease."
)

# 3) Iterate and build JSONL records
with open("output.jsonl", "w") as fout:
    for _, row in df.iterrows():
        # You can swap in whichever columns make sense—
        # here we use 'vignette' plus (optionally) a disease column.
        vignette = row.get("vignette", "").strip()
        # If you have a 'disease' column, use it. Otherwise leave blank or fill in manually.
        disease = row.get("disease", "").strip()

        # Build the “input” string
        input_parts = []
        if vignette:
            input_parts.append(vignette)
        if disease:
            input_parts.append(
                f"\n\nThis is the disease which you are to increase the probability of: {disease}"
            )
        input_text = "".join(input_parts)

        record = {
            "instruction": INSTRUCTION,
            "input": input_text,
            "output": "",  # <-- fill this in later, or hook up your model
        }
        fout.write(json.dumps(record, ensure_ascii=False) + "\n")

print("Wrote", len(df), "records to output.jsonl")

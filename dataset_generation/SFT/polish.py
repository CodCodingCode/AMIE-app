import json

input_path  = "combined_dataset.jsonl"
output_path = "combined_dataset_clean.jsonl"

with open(input_path, "r") as fin, open(output_path, "w") as fout:
    for i, line in enumerate(fin, start=1):
        line = line.strip()
        if line == "{}":
            # skip totally empty JSON objects
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as e:
            print(f"⚠️  Skipping malformed JSON at line {i}: {e}")
            continue
        # drop any keys whose value is empty string
        cleaned = {k: v for k, v in record.items() if v != ""}
        if not cleaned:
            # skip records that became empty after stripping out empty strings
            continue
        fout.write(json.dumps(cleaned, ensure_ascii=False) + "\n")

print(f"✅ Cleaned dataset written to {output_path}")
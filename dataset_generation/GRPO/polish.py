import json

input_path = "combined_dataset.jsonl"
output_path = "combined_dataset_clean.jsonl"

with open(input_path, "r") as fin, open(output_path, "w") as fout:
    for line in fin:
        record = json.loads(line)
        # remove any key whose value is "" (empty string)
        cleaned = {k: v for k, v in record.items() if v != ""}
        # if you want to drop entire records that now have no fields left:
        # if not cleaned:
        #     continue
        fout.write(json.dumps(cleaned, ensure_ascii=False) + "\n")

print(f"Done — cleaned records written to {output_path}")
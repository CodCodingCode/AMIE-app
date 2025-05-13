import json
import csv
from pathlib import Path

# ────────── 0. CONFIGURE INPUT / OUTPUT FILES ──────────
INFILE = Path(
    "/Users/owner/Downloads/coding projects/AMIE-app/results.json"
)  # your source JSON
OUTFILE = Path("io_pairs.jsonl")  # where to write input/output JSONL


# ────────── 1. PROCESS JSON → JSONL ──────────
def process_json(infile: Path, outfile: Path):
    with infile.open("r", encoding="utf-8") as fin, outfile.open(
        "w", encoding="utf-8"
    ) as fout:
        data = json.load(fin)
        for rec in data:
            out_rec = {
                "input": rec["doctor_vignette"],
                "output": rec["ruling_out_question"].strip('"'),
            }
            fout.write(json.dumps(out_rec, ensure_ascii=False) + "\n")


# ────────── 2. (Optional) PROCESS CSV → JSONL ──────────
def process_csv(infile: Path, outfile: Path):
    with infile.open(newline="", encoding="utf-8") as fin, outfile.open(
        "w", encoding="utf-8"
    ) as fout:
        reader = csv.DictReader(fin)
        for rec in reader:
            out_rec = {
                "input": rec["doctor_vignette"],
                "output": rec["ruling_out_question"].strip('"'),
            }
            fout.write(json.dumps(out_rec, ensure_ascii=False) + "\n")


# ────────── 3. MAIN ENTRYPOINT ──────────
def main():
    suffix = INFILE.suffix.lower()
    if suffix == ".json":
        process_json(INFILE, OUTFILE)
    elif suffix in {".csv", ".tsv"}:
        process_csv(INFILE, OUTFILE)
    else:
        raise RuntimeError("Unsupported input format: " + suffix)
    print(f"✅ Wrote I/O pairs to {OUTFILE}")


if __name__ == "__main__":
    main()

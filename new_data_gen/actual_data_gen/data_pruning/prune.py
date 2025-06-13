import os
import json
import glob

# -- CONFIGURE THESE --
BASE_DIR = (
    "/Users/owner/Downloads/coding projects/AMIE-app/"  # change to your project root
)
FOLDERS = [
    "2diagnosing_doctor_outputs",
    "2patient_followups",
    "2questioning_doctor_outputs",
    "2summarizer_outputs",
    "2treatment_plans",
    "2behavioral_analyses",
]
QUESTION_DIR = os.path.join(BASE_DIR, "2questioning_doctor_outputs")
# ----------------------


def find_bad_indices():
    bad = set()
    for path in glob.glob(os.path.join(QUESTION_DIR, "*.json")):
        try:
            with open(path, "r") as f:
                data = json.load(f)
        except Exception:
            continue
        for entry in data:
            inp = str(entry.get("input", "")).lower()
            out = str(entry.get("output", "")).lower()
            if "gold" in inp or "gold" in out:
                # assume each entry has a vignette_index field
                idx = entry.get("vignette_index")
                if idx is None:
                    # fallback: extract from filename like questioner_123.json
                    fname = os.path.basename(path)
                    parts = fname.split("_")
                    if len(parts) >= 2 and parts[-1].endswith(".json"):
                        idx = int(parts[-1][:-5])
                bad.add(idx)
                break
    return bad


def prune_indices(bad_indices):
    for folder in FOLDERS:
        folder_path = os.path.join(BASE_DIR, folder)
        for idx in bad_indices:
            pattern = os.path.join(folder_path, f"*_{idx}.json")
            for p in glob.glob(pattern):
                print(f"Removing {p}")
                os.remove(p)


if __name__ == "__main__":
    bad = find_bad_indices()
    print(f"Found {len(bad)} bad indices:", bad)
    prune_indices(bad)
    print("Done pruning.")

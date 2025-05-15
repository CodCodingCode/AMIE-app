import json
import os

# Input folder containing all JSON/JSONL files
input_folder = "/Users/owner/Downloads/coding projects/AMIE-app/datasets/SFT"
# Output JSONL file path
output_jsonl_path = "/Users/owner/Downloads/coding projects/AMIE-app/datasets/combined_dataset.jsonl"

def load_json_file(file_path):
    """Load a JSON or JSONL file and return its list of entries."""
    data = []
    with open(file_path, "r", encoding="utf-8") as f:
        # peek first non-whitespace character
        first_char = None
        while True:
            c = f.read(1)
            if not c:
                break
            if not c.isspace():
                first_char = c
                break
        f.seek(0)
        if first_char == "[":
            # entire file is a JSON array
            try:
                data = json.load(f)
            except json.JSONDecodeError as e:
                print(f"⚠️ Failed to parse JSON array in {file_path}: {e}")
                data = []
        else:
            # treat as JSONL
            for i, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    data.append(json.loads(line))
                except json.JSONDecodeError as e:
                    print(f"⚠️ Skipping malformed JSON at line {i} of {file_path}: {e}")
    print(f"Loaded {len(data)} entries from {file_path}")
    return data

def format_entry(entry):
    """Ensure each entry has the required 'instruction', 'input', and 'output' fields."""
    return {
        "instruction": entry.get("instruction", ""),
        "input":       entry.get("input", ""),
        "output":      entry.get("output", ""),
    }


def merge_datasets(input_folder, output_jsonl_path):
    combined_data = []
    for file_name in os.listdir(input_folder):
        file_path = os.path.join(input_folder, file_name)
        if not (file_name.endswith(".json") or file_name.endswith(".jsonl")):
            print(f"Skipping non-JSON file: {file_name}")
            continue
        entries = load_json_file(file_path)
        for entry in entries:
            combined_data.append(format_entry(entry))

    with open(output_jsonl_path, "w", encoding="utf-8") as out:
        for entry in combined_data:
            out.write(json.dumps(entry, ensure_ascii=False) + "\n")

    print(f"Combined dataset saved to {output_jsonl_path} with {len(combined_data)} entries")

if __name__ == "__main__":
    merge_datasets(input_folder, output_jsonl_path)
import json
import os
import re

"""
This script reads a JSON array of SNOMED-CT entries (like "[SNOMED-CT] 10029008: Suicide precautions"),
parses each code and display text, and generates one Synthea keep-module JSON file per code.

Save your list of entries as `snomed_codes.json` in the same folder, then run:

    python generate_synthea_modules.py

The modules will be written under `output/` as `module_<code>.json`.
"""


def parse_entry(entry: str):
    """
    Parse a single entry of the form "[SNOMED-CT] CODE: Display Text"
    Returns (code, display) or (None, None) on failure.
    """
    m = re.match(r"\[SNOMED-CT\]\s*(?P<code>\d+):\s*(?P<display>.+)", entry)
    if not m:
        return None, None
    return m.group("code"), m.group("display")


def make_module(code: str, display: str):
    """
    Build a Synthea keep-module dict for this SNOMED-CT code.
    """
    return {
        "name": f"Generated Keep Module {code}",
        "states": {
            "Initial": {
                "type": "Initial",
                "name": "Initial",
                "conditional_transition": [
                    {
                        "transition": "Keep",
                        "condition": {
                            "condition_type": "And",
                            "conditions": [
                                {
                                    "condition_type": "Active Condition",
                                    "codes": [
                                        {
                                            "system": "SNOMED-CT",
                                            "code": code,
                                            "display": display,
                                        }
                                    ],
                                }
                            ],
                        },
                    },
                    {"transition": "Terminal"},
                ],
            },
            "Terminal": {"type": "Terminal", "name": "Terminal"},
            "Keep": {"type": "Terminal", "name": "Keep"},
        },
        "gmf_version": 2,
    }


def main():
    # load the code list
    with open("snomed_codes.json", "r") as f:
        entries = json.load(f)

    os.makedirs("output", exist_ok=True)
    count = 0
    for entry in entries:
        code, display = parse_entry(entry)
        if not code:
            continue
        module = make_module(code, display)
        out_file = os.path.join("output", f"module_{code}.json")
        with open(out_file, "w") as wf:
            json.dump(module, wf, indent=2)
        count += 1

    print(f"Generated {count} Synthea modules in 'output/' directory.")


if __name__ == "__main__":
    main()

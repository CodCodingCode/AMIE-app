import re
import json
import os

# Define paths to the JSON files
files = {
    "“You are a clinical summarizer. Given a transcript of a doctor–patient dialogue, extract a structured clinical vignette summarizing the key symptoms, relevant history, and any diagnostic clues.”": "all_summarizer_outputs.json",
    "You are a board-certified clinician. Based on the provided diagnosis and patient vignette, propose a realistic, evidence-based treatment plan suitable for initiation by a primary care physician or psychiatrist.": "all_treatment_outputs.json",
    "You are a diagnostic reasoning model (Early Stage). Based on the patient vignette and early-stage observations, generate a list of plausible diagnoses with reasoning. Focus on broad differentials, considering common and uncommon conditions.": "split_outputs_DD_E.json",
    "You are a diagnostic reasoning model (Middle Stage). Given the current vignette, prior dialogue, and diagnostic hypothesis, refine the list of possible diagnoses with concise justifications for each. Aim to reduce diagnostic uncertainty.": "split_outputs_DD_M.json",
    "You are a diagnostic reasoning model (Late Stage). Based on the final patient vignette summary and full conversation, provide the most likely diagnosis with structured reasoning. Confirm diagnostic certainty and include END if no more questioning is necessary.": "split_outputs_DD_L.json",
    "You are a questioning agent (Early Stage). Your task is to propose highly relevant early-stage questions that can open the differential diagnosis widely. Use epidemiology, demographics, and vague presenting symptoms as guides.": "split_outputs_DQ_E.json",
    "You are a questioning agent (Middle Stage). Using the current diagnosis, past questions, and patient vignette, generate a specific question to refine the current differential diagnosis. Return your reasoning and next question.": "split_outputs_DQ_M.json",
    "You are a questioning agent (Late Stage). Based on narrowed differentials and previous dialogue, generate a focused question that would help confirm or eliminate the final 1-2 suspected diagnoses.": "split_outputs_DQ_L.json",
}

combined_data = []

# Load and reformat each file
for instruction, filename in files.items():
    if not os.path.exists(filename):
        print(f"File not found: {filename}")
        continue
    with open(filename, "r") as f:
        entries = json.load(f)
        for entry in entries:
            combined_data.append(
                {
                    "instruction": instruction,
                    "input": re.sub(r"^\s*\d+\.\s*", "", entry.get("input", "")),
                    "output": entry.get("output", ""),
                }
            )

# Save combined output
with open("combined_conversations.json", "w") as f:
    json.dump(combined_data, f, indent=2)

print("✅ Combined JSON written to combined_conversations.json")

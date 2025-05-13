import pandas as pd
from openai import OpenAI
import time

# Load your merged CSV
df = pd.read_csv("dataset_generation/SFT/ACI-Bench/clef_taskC_test3_merged_all.csv")

# Only fill string-type columns to avoid dtype warnings
df = df.fillna(value={col: "" for col in df.select_dtypes(include=["object"]).columns})

# OpenAI client setup (new SDK style)
api_key = "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"  # your actual key
client = OpenAI(api_key=api_key)


# Prompt template
def format_prompt(row):
    return f"""
You are a clinical summarizer. Write a patient vignette based on the following structured data:

- Name: {row['patient_firstname']} {row['patient_familyname']}
- Age: {row['patient_age']}
- Gender: {row['patient_gender']}
- Chief Complaint: {row['cc']}
- Secondary Complaints: {row['2nd_complaints']}
- Clinical Note: {row['note']}
- Dialogue Transcript: {row['dialogue']}

Please generate a concise, readable vignette that captures the clinical picture, suitable for use in a medical case review or clinical reasoning dataset. Please make the vignette in paragraph format. 
"""


# ChatGPT call with new SDK (OpenAI client)
def get_chatgpt_vignette(prompt, model="gpt-4.1-mini", max_retries=3):
    for _ in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print("Retrying after error:", e)
            time.sleep(3)
    return "Vignette generation failed."


# Generate vignettes
vignettes = []
for idx, row in df.iterrows():
    prompt = format_prompt(row)
    vignette = get_chatgpt_vignette(prompt)
    vignettes.append(vignette)
    print(f"✅ Row {idx+1} vignette created")

# Save to CSV
df["vignette"] = vignettes
df.to_csv("clef_taskC_test3_with_chatgpt_vignettes2.csv", index=False)
print("✅ All vignettes saved to clef_taskC_test3_with_chatgpt_vignettes.csv")

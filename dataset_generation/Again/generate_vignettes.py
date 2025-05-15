import pandas as pd
import os
import json
import time
from openai import OpenAI

# Load dataset
import kagglehub

path = kagglehub.dataset_download("dhivyeshrk/diseases-and-symptoms-dataset")
files = [f for f in os.listdir(path) if f.endswith(".csv")]
dataset_path = os.path.join(path, files[0])
df = pd.read_csv(dataset_path)

# Extract unique diseases
unique_diseases = df["diseases"].dropna().unique()

# Initialize OpenAI client
client = OpenAI(
    api_key=key
)
model = "gpt-4.1-mini"

# Output storage
all_vignettes = {}

prev_responses = []
# Generation loop
for disease in unique_diseases:
    for i in range(10):
        prompt = f"""
    You are a medical expert. Generate a detailed and realistic patient vignettes for the following disease: **{disease}**.

    Each vignette should:
    - Be 8 sentences long
    - Include symptoms, age, gender (random), and clinical context
    - Be medically plausible
    - Avoid repeating the vignettes from previous iterations: {prev_responses}

    Format your response as a numbered list.
        """

        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert medical diagnostician.",
                },
                {"role": "user", "content": prompt},
            ],
        )
        vignettes_text = response.choices[0].message.content
        all_vignettes[disease] = vignettes_text

        prev_responses.append(vignettes_text)

        print(f"✅ Generated for: {disease}")
        time.sleep(1.2)  # Respect rate limits
    prev_responses = []

# Save all to JSON
with open("disease_vignettes.json", "w") as f:
    json.dump(all_vignettes, f, indent=2)

print("🎉 Vignettes saved to 'disease_vignettes.json'")

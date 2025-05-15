import json
import os
import time
from openai import OpenAI
from concurrent.futures import ThreadPoolExecutor, as_completed

# Load JSON file with disease entries
with open(
    "/Users/owner/Downloads/coding projects/AMIE-app/dataset_generation/Again/familydoctor_conditions.json",
    "r",
) as f:
    disease_entries = json.load(f)

# Initialize OpenAI client
client = OpenAI(
    api_key="api_key_here",  # Replace with your actual key
)  # Replace with your actual key
model = "gpt-4.1-mini"

# Output storage
all_vignettes = {}
prev_responses = []


# Function to generate a single vignette
def generate_vignette(disease, article_text, prev_responses_snapshot):
    prompt = f"""
You are a medical expert. Generate a detailed and realistic patient vignette for the following condition: **{disease}**.

Each vignette should:
- Be 8 sentences long
- Include symptoms, age, gender (random), and clinical context
- Be medically plausible
- Be informed by the following article content (if relevant):
{article_text[:1500]}...

Avoid repeating the vignettes from previous iterations: {prev_responses_snapshot}

Format your response as a numbered vignette.
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

    return response.choices[0].message.content.strip()


# Generation loop
for entry in disease_entries:
    disease = entry.get("list_title", "").strip()
    article_text = entry.get("article_text", "").strip()

    if not disease or not article_text:
        continue

    all_vignettes[disease] = []

    # Use threads to generate 10 vignettes in parallel
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [
            executor.submit(
                generate_vignette, disease, article_text, prev_responses[-3:]
            )
            for _ in range(10)
        ]
        for future in as_completed(futures):
            vignette_text = future.result()
            all_vignettes[disease].append(vignette_text)
            prev_responses.append(vignette_text)
            print(f"✅ Generated vignette for: {disease}")

    prev_responses = []

# Save all vignettes to JSON
with open("disease_vignettes_from_familydoctor.json", "w") as f:
    json.dump(all_vignettes, f, indent=2)

print("🎉 Vignettes saved to 'disease_vignettes_from_familydoctor.json'")

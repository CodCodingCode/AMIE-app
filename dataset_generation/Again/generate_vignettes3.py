import os
import json
from openai import OpenAI
from concurrent.futures import ThreadPoolExecutor, as_completed

# Initialize OpenAI client
client = OpenAI(api_key="api-key-here")
model = "gpt-4.1-mini"

# Load diseases from malacards-diseases.json
with open("malacards-diseases.json", "r") as f:
    json_data = json.load(f)

# Output storage
all_vignettes = {}


def check_and_generate_vignettes(disease):
    # Step 1: Ask GPT if it's a real disease
    check_prompt = f"Is '{disease}' a medically recognized disease or disorder? Answer only 'Yes' or 'No'."
    try:
        check_response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a medical expert."},
                {"role": "user", "content": check_prompt},
            ],
        )
        is_valid = (
            check_response.choices[0].message.content.strip().lower().startswith("yes")
        )
    except Exception as e:
        print(f"❌ Error checking disease '{disease}': {e}")
        return disease, "NO"

    if not is_valid:
        return disease, "NO"

    # Step 2: Generate 10 vignettes
    local_vignettes = []
    prev_responses = []
    for _ in range(4):
        prompt = f"""
You are a medical expert. Generate a detailed and realistic patient vignette for the following disease: **{disease}**.

Each vignette should:
- Be 8 sentences long
- Include symptoms, age, gender (random), and clinical context
- Be medically plausible
- Avoid repeating the vignettes from previous iterations: {prev_responses}

Format your response as a numbered list.
        """
        try:
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
            vignette_text = response.choices[0].message.content
            local_vignettes.append(vignette_text)
            prev_responses.append(vignette_text)
        except Exception as e:
            print(f"❌ Error generating vignette for '{disease}': {e}")
            return disease, "NO"
    return disease, local_vignettes


# Run in parallel
with ThreadPoolExecutor(max_workers=12) as executor:
    futures = [
        executor.submit(check_and_generate_vignettes, item["disease"])
        for item in json_data
    ]
    for future in as_completed(futures):
        disease, result = future.result()
        all_vignettes[disease] = result

        # Save incrementally
        with open("validated_disease_vignettes.json", "w") as f:
            json.dump(all_vignettes, f, indent=2)
        print(
            f"✅ Processed: {disease} ({'vignettes generated' if result != 'NO' else 'invalid disease'})"
        )

print("🎉 All results saved to 'validated_disease_vignettes.json'")

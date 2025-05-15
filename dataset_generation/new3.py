from openai import OpenAI
import json
import os
import time
from api_key import key  # Assuming you have this file with the API key

# Initialize OpenAI client
API_KEY = key
client = OpenAI(api_key=API_KEY)


def load_results(filename="results.json"):
    """Load clinical cases from the results JSON file"""
    try:
        with open(filename, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading results file: {e}")
        return []


def generate_wrong_diagnoses(vignette, actual_diagnosis, model="gpt-4o-mini"):
    """Generate plausible but incorrect diagnoses using OpenAI API"""
    prompt = f"""You are given a clinical vignette describing a patient's condition. Your task is to generate the most likely disease that is **plausible but incorrect** diagnoses for this case.

Make sure:
- The diseases are medically real
- The diseases are not even CLOSE to the correct diagnosis

Please format the response with:

THINKING: Insert here your reasoning for your diagnosis 

DIAGNOSES: Insert here your Diagnosis

Vignette:
{vignette}

Correct diagnosis:
{actual_diagnosis}"""

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

        # Extract and clean up the response
        content = response.choices[0].message.content

        # Parse the numbered list - extract just the diagnoses
        diagnoses = []
        for line in content.strip().split("\n"):
            line = line.strip()
            if line and any(line.startswith(f"{i}.") for i in range(1, 11)):
                diagnosis = line.split(".", 1)[1].strip()
                diagnoses.append(diagnosis)

        return diagnoses
    except Exception as e:
        print(f"Error generating wrong diagnoses: {e}")
        return []


def main():
    # Load the existing results file
    results = load_results()
    if not results:
        print("No results found in results.json")
        return

    print(f"Loaded {len(results)} cases from results.json")

    # Create a new output list
    output_data = []

    # Process each case
    for idx, case in enumerate(results, 1):
        print(f"\nProcessing case {idx}/{len(results)}")

        # Extract the required information
        vignette = case.get("doctor_vignette", "")
        actual_diagnosis = case.get("actual_diagnosis", "")

        if not vignette or not actual_diagnosis:
            print(f"Missing vignette or diagnosis for case {idx}, skipping...")
            continue

        print(f"Generating wrong diagnoses for case with diagnosis: {actual_diagnosis}")

        # Generate wrong diagnoses
        wrong_diagnoses = generate_wrong_diagnoses(vignette, actual_diagnosis)

        if wrong_diagnoses:
            print(f"Generated {len(wrong_diagnoses)} incorrect diagnoses")

            # Create output structure
            case_output = {
                "case_number": case.get("case_number", idx),
                "vignette": vignette,
                "actual_diagnosis": actual_diagnosis,
                "wrong_diagnoses": wrong_diagnoses,
            }

            output_data.append(case_output)

            # Print the generated wrong diagnoses
            print("\nWrong diagnoses:")
            for i, diagnosis in enumerate(wrong_diagnoses, 1):
                print(f"{i}. {diagnosis}")
        else:
            print("Failed to generate wrong diagnoses for this case")

        # Add a small delay to avoid hitting API rate limits
        time.sleep(1)

    # Save the output to a new file
    output_file = "wrong_diagnoses_results.json"
    with open(output_file, "w") as f:
        json.dump(output_data, f, indent=2)

    print(f"\nProcessed {len(output_data)} cases successfully.")
    print(f"Results saved to {output_file}")


if __name__ == "__main__":
    main()

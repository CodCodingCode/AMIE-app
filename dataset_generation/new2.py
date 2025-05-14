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


def generate_low_quality_question(vignette, question, model="gpt-4o-mini"):
    """Generate a low-quality follow-up question using OpenAI API"""
    prompt = f"""You are helping build a medical dataset to train an AI assistant. You are given a doctor's vignette describing a patient.

Your task is to generate the reasoning for the following question: 
Good Question:
{question}

1. Making the question not really oritneded to the vignette
2. Making the question not really useful for diagnosis

Only give one question as your answer.

Vignette:
{vignette}

Good Question:
{question}
"""

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert in creating medical training datasets.",
                },
                {"role": "user", "content": prompt},
            ],
        )

        # Extract and clean up the response
        question = response.choices[0].message.content.strip()
        return question
    except Exception as e:
        print(f"Error generating low-quality question: {e}")
        return ""


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
        question = case.get("ruling_out_question", "")
        actual_diagnosis = case.get("actual_diagnosis", "")

        if not vignette:
            print(f"Missing vignette for case {idx}, skipping...")
            continue

        print(f"Generating low-quality question for case...")

        # Generate low-quality question
        question = generate_low_quality_question(vignette, question)

        if question:
            print(f"Generated low-quality question")

            # Create output structure
            case_output = {
                "case_number": case.get("case_number", idx),
                "vignette": vignette,
                "actual_diagnosis": actual_diagnosis,
                "low_quality_question": question,
            }

            output_data.append(case_output)

            # Print the generated question
            print(f"\nLow-quality question: {question}")
        else:
            print("Failed to generate question for this case")

        # Add a small delay to avoid hitting API rate limits
        time.sleep(1)

    # Save the output to a new file
    output_file = "low_quality_questions.json"
    with open(output_file, "w") as f:
        json.dump(output_data, f, indent=2)

    print(f"\nProcessed {len(output_data)} cases successfully.")
    print(f"Results saved to {output_file}")


if __name__ == "__main__":
    main()

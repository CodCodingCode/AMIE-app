import json
import os
from openai import OpenAI
from typing import List, Dict, Any
import time
import sys

# Fix the API key handling
# The previous code was incorrectly using os.environ.get() with the actual API key as the parameter
# Instead, either directly use a string or properly get it from environment variables
api_key = api_key

# Verify API key is valid
if not api_key:
    print("Error: API key is not set. Please provide a valid OpenAI API key.")
    sys.exit(1)


def extract_cumulative_qa(data_entry: Dict[str, Any]) -> str:
    """Extract the original vignette and all questions and answers from a data entry."""
    input_text = data_entry["input"]

    # Split the input text into lines
    lines = input_text.split("\n")

    # The first line is typically the initial patient vignette
    vignette = lines[0]

    # Construct the full text with all Q&A
    full_text = vignette + "\n\n"

    # Extract questions and answers
    qa_pairs = []
    current_q = ""
    for line in lines[1:]:
        if line.startswith("Question: "):
            current_q = line.replace("Question: ", "")
        elif line.startswith("Answer: ") and current_q:
            current_a = line.replace("Answer: ", "")
            qa_pairs.append((current_q, current_a))
            current_q = ""

    # Format Q&A for better readability
    for q, a in qa_pairs:
        full_text += f"Q: {q}\nA: {a}\n\n"

    return full_text


def generate_vignette_summary(qa_text: str, retries=3) -> str:
    """Use GPT to summarize Q&A into a coherent patient vignette."""
    attempt = 0
    while attempt < retries:
        try:
            client = OpenAI(api_key=api_key)
            
            print(f"Making API call to summarize text (attempt {attempt+1}/{retries})...")
            response = client.chat.completions.create(
                model="gpt-4o",  # or another available model
                messages=[
                    {
                        "role": "system",
                        "content": "You are a summarization tool. Please summarize this short patient vignette and questions and answers into one detailed patient vignette.",
                    },
                    {"role": "user", "content": qa_text},
                ],
                max_tokens=1000,
                temperature=0.3,
                timeout=60,  # Add a timeout to prevent hanging indefinitely
            )
            result = response.choices[0].message.content.strip()
            print(f"Successfully generated summary ({len(result)} chars)")
            return result
            
        except Exception as e:
            attempt += 1
            print(f"Error generating summary (attempt {attempt}/{retries}): {e}")
            if attempt < retries:
                sleep_time = 5 * attempt  # Exponential backoff
                print(f"Retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)
            else:
                print("Failed to generate summary after multiple attempts")
                return ""


def create_instruction_dataset(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Create an instruction dataset for fine-tuning."""
    instruction_dataset = []
    
    total_entries = len(data)
    for i, entry in enumerate(data):
        print(f"Processing entry {i+1}/{total_entries}")
        
        # Extract the original vignette and Q&A
        full_qa_text = extract_cumulative_qa(entry)
        
        # Generate the summarized vignette
        print(f"Generating summary for entry {i+1}...")
        summarized_vignette = generate_vignette_summary(full_qa_text)
        
        if summarized_vignette:
            instruction_dataset.append(
                {
                    "instruction": "You are a summarization tool. Please summarize this short patient vignette and questions and answers into one detailed patient vignette.",
                    "input": full_qa_text,
                    "output": summarized_vignette,
                }
            )
            
            # Save intermediate results after each successful entry
            if (i + 1) % 5 == 0:
                intermediate_file = "/Users/owner/Downloads/coding projects/AMIE-app/datasets/vignette_instruction_dataset_partial.json"
                try:
                    with open(intermediate_file, "w", encoding="utf-8") as f:
                        json.dump(instruction_dataset, f, indent=2, ensure_ascii=False)
                    print(f"Saved intermediate results ({len(instruction_dataset)} entries)")
                except Exception as e:
                    print(f"Warning: Couldn't save intermediate results: {e}")
            
            # Add a short delay to avoid rate limiting
            time.sleep(1)
        else:
            print(f"Warning: Failed to generate summary for entry {i+1}, skipping")

    return instruction_dataset


def process_dataset(input_file: str, output_file: str):
    """Process the dataset and save the results."""
    try:
        # Load the original dataset
        with open(input_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        print(f"Loaded {len(data)} entries from {input_file}")

        # Create the instruction dataset
        instruction_dataset = create_instruction_dataset(data)

        # Save the instruction dataset
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(instruction_dataset, f, indent=2, ensure_ascii=False)

        print(f"Saved {len(instruction_dataset)} entries to {output_file}")

    except Exception as e:
        print(f"Error processing dataset: {e}")


if __name__ == "__main__":
    input_file = (
        "/Users/owner/Downloads/coding projects/AMIE-app/datasets/full_dataset.json"
    )
    output_file = "/Users/owner/Downloads/coding projects/AMIE-app/datasets/vignette_instruction_dataset.json"

    # Make sure the output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    process_dataset(input_file, output_file)

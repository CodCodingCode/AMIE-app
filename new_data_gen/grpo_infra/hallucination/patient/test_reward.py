import requests
import json
import os
import random
from datetime import datetime
import re

# ============================================================================
# REPLACE THESE WITH YOUR ACTUAL VALUES
# ============================================================================
ENDPOINT_URL = "url"  # Your endpoint URL from the screenshot
HF_TOKEN = "url"  # Your HuggingFace token
VIGNETTES_FILE = "new_data_gen/actual_data_gen/disease_vignettes_from_familydoctor.json"  # Your JSON file with the vignettes


class HuggingFaceInference:
    def __init__(self, endpoint_url, api_token):
        self.endpoint_url = endpoint_url
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
        }

    def generate(self, prompt, max_new_tokens=800):
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": max_new_tokens,
                "temperature": 0.7,
                "do_sample": True,
                "return_full_text": True,
            },
        }

        try:
            response = requests.post(
                self.endpoint_url, headers=self.headers, json=payload
            )
            response.raise_for_status()

            result = response.json()

            # Handle the response format
            if isinstance(result, list) and len(result) > 0:
                generated_text = result[0].get("generated_text", "")
            else:
                generated_text = str(result)

            return generated_text

        except requests.exceptions.RequestException as e:
            print(f"❌ API request failed: {e}")
            if hasattr(e, "response") and e.response is not None:
                print(f"Status: {e.response.status_code}")
                print(f"Response: {e.response.text}")
            raise


# Initialize the inference client
model_client = HuggingFaceInference(ENDPOINT_URL, HF_TOKEN)


def load_vignettes(filename):
    """Load vignettes from JSON file and select 2 per condition"""
    try:
        with open(filename, "r") as f:
            data = json.load(f)

        selected_vignettes = {}
        for condition, vignettes in data.items():
            cleaned_vignettes = []
            for vignette in vignettes:
                if isinstance(vignette, str):
                    cleaned_vignette = re.sub(r"^(\d+\.\s+)", "", vignette.strip())
                    cleaned_vignettes.append(cleaned_vignette)
                else:
                    cleaned_vignettes.append(str(vignette))
            # Take only first 2 vignettes per condition
            selected_vignettes[condition] = cleaned_vignettes[:2]
            print(
                f"📋 Loaded {len(selected_vignettes[condition])} vignettes for {condition}"
            )

        return selected_vignettes
    except FileNotFoundError:
        print(f"❌ Vignettes file {filename} not found!")
        return {}
    except json.JSONDecodeError:
        print(f"❌ Invalid JSON in {filename}")
        return {}


def get_random_vignette():
    """Get a random vignette from the loaded vignettes"""
    vignettes_data = load_vignettes(VIGNETTES_FILE)
    if not vignettes_data:
        return "A patient presents with concerning symptoms.", "Unknown Condition"

    # Get all vignettes from all conditions with their condition names
    all_vignettes_with_conditions = []
    for condition, vignettes in vignettes_data.items():
        for vignette in vignettes:
            all_vignettes_with_conditions.append((vignette, condition))

    selected_vignette, condition = random.choice(all_vignettes_with_conditions)
    return selected_vignette, condition


# ─── ChatGPT Reward Function ────────────────────────────────────────
from openai import OpenAI
import time
import multiprocessing
import shutil
from itertools import islice

# Initialize OpenAI client
client = OpenAI(
    api_key="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"
)
model = "gpt-4o-mini"


def chatgpt_hallucination_reward(prompts, completions, vignette, **kwargs):
    rewards = []
    for idx, (prompt, completion) in enumerate(zip(prompts, completions)):

        # Extract patient input from prompt if it's a clinical summarizer task
        if "clinical summarizer" in prompt.lower():
            input_match = re.search(
                r"Input:\s*(.*?)\s*(?:Previous Vignette|Output:|$)", prompt, re.DOTALL
            )
            if input_match:
                patient_input = input_match.group(1).strip()

                # Create ChatGPT prompt to evaluate hallucination
                evaluation_prompt = f"""
You are an expert clinical fact-checker. Your job is to compare a patient's original statement with a clinical summary and identify any hallucinations or inaccuracies.

PATIENT'S ORIGINAL STATEMENT:
{patient_input}

CLINICAL SUMMARY TO EVALUATE:
{completion}

Please analyze if the clinical summary adds any information that was NOT mentioned by the patient AND if it missed any important information that WAS mentioned by the patient. Look for:

HALLUCINATIONS (things added that patient never said):
1. Symptoms the patient never mentioned
2. Demographic information that contradicts what the patient said
3. Severity descriptions not provided by the patient
4. Any other fabricated details

OMISSIONS (important things the patient said but the summary missed):
1. Key symptoms mentioned by patient but not included in summary
2. Important demographic details the patient provided
3. Relevant history or context the patient shared
4. Timeline information the patient specified

Respond with a JSON object containing:
- "hallucinated_items": [list of specific things that were added/fabricated]
- "omitted_items": [list of important things patient said but summary missed]
- "accurate_items": [list of things correctly extracted from patient statement]
- "score": a number from -10 to +10 (-10 = severe hallucination/omissions, +10 = perfect accuracy)

Scoring guidance:
- Deduct 3 points for each hallucinated item
- Deduct 1 point for each important omitted item  
- Add 1 point for each accurate item
- Perfect extraction with no hallucinations or omissions = +10

Example response:
{{"hallucinated_items": ["dizziness", "repeated vomiting"], "omitted_items": ["family history of migraines"], "accurate_items": ["17-year-old female", "left-sided headache", "photophobia"], "score": -2}}
"""

                try:
                    response = client.chat.completions.create(
                        model=model,
                        messages=[{"role": "user", "content": evaluation_prompt}],
                        temperature=0.1,
                        max_tokens=500,
                    )

                    # Parse the response
                    result = json.loads(response.choices[0].message.content)
                    score = result.get("score", 0.0)
                    hallucinated = result.get("hallucinated_items", [])
                    accurate = result.get("accurate_items", [])

                    print(
                        f"[debug reward] #{idx} → hallucinated: {hallucinated}, accurate: {accurate}, score: {score}"
                    )

                except Exception as e:
                    print(
                        f"[debug reward] #{idx} → ChatGPT error: {e}, defaulting to 0.0"
                    )
                    score = 0.0

            else:
                score = 0.0
        else:
            score = 0.0

        rewards.append(score)
    return rewards


def test_reward_function_with_vignettes():
    """Test the ChatGPT reward function with vignettes"""

    print("🧪 Testing ChatGPT Reward Function with Vignettes")
    print("=" * 60)

    # Load vignettes
    vignettes_data = load_vignettes(VIGNETTES_FILE)
    if not vignettes_data:
        print("No vignettes loaded. Please check your vignettes file.")
        return

    test_count = 0

    # Test with multiple vignettes
    for condition, vignettes in vignettes_data.items():
        print(f"\n🔍 Testing condition: {condition}")

        for vignette_index, vignette in enumerate(vignettes):
            test_count += 1
            print(
                f"\n📋 Test {test_count}: {condition} - Vignette {vignette_index + 1}"
            )
            print(f"Vignette: {vignette[:100]}...")

            # Create a test patient response based on the vignette
            test_patient_input = f"Well, doctor, {vignette[:200]}..."

            # Create test prompt
            test_prompt = f"""
Instruction: You are a patient agent. Please act as if you are a real patient with the following vignette and conversation.
Input: {test_patient_input} Previous Vignette: 
Output: THINKING: 
"""

            print("🔄 Generating clinical summary with your model...")
            model_output = model_client.generate(test_prompt, max_new_tokens=400)

            print("📋 Model Output:")
            print(
                model_output[:300] + "..." if len(model_output) > 300 else model_output
            )
            print("\n" + "-" * 50)

            # Test the reward function
            print("🔄 Testing reward function...")
            rewards = chatgpt_hallucination_reward(
                [test_prompt], [model_output], vignette
            )

            print(f"🎯 Reward Score: {rewards[0]}")
            print("-" * 50)

            # Limit to 5 tests for demo
            if test_count >= 5:
                break

        if test_count >= 5:
            break

    print(f"\n✅ Completed {test_count} tests with vignettes!")


def test_all_conditions():
    """Test all conditions with 2 vignettes each"""

    print("🧪 Testing All Conditions")
    print("=" * 60)

    # Load vignettes
    vignettes_data = load_vignettes(VIGNETTES_FILE)
    if not vignettes_data:
        print("No vignettes loaded. Please check your vignettes file.")
        return

    all_results = []

    for condition, vignettes in vignettes_data.items():
        print(f"\n🔍 Testing condition: {condition}")
        condition_results = []

        for vignette_index, vignette in enumerate(vignettes):
            print(f"📋 Vignette {vignette_index + 1}/{len(vignettes)}")

            # Create a test patient response based on the vignett

            # Create test prompt
            test_prompt = f"""
Instruction: You are a clinical summarizer. Given a transcript of a doctor–patient dialogue, extract a structured clinical vignette summarizing the key symptoms, relevant history, and any diagnostic clues.
Input: {vignette} what brings you in today?
Output: THINKING: 
"""

            try:
                model_output = model_client.generate(test_prompt, max_new_tokens=400)
                rewards = chatgpt_hallucination_reward(
                    [test_prompt], [model_output], vignette
                )

                result = {
                    "condition": condition,
                    "vignette_index": vignette_index,
                    "score": rewards[0],
                    "vignette": vignette[:100] + "...",
                }

                condition_results.append(result)
                print(f"  Score: {rewards[0]}")

            except Exception as e:
                print(f"  ❌ Error: {e}")
                continue

        all_results.extend(condition_results)

        # Calculate average for this condition
        if condition_results:
            avg_score = sum(r["score"] for r in condition_results) / len(
                condition_results
            )
            print(f"📊 Average score for {condition}: {avg_score:.2f}")

    # Save results
    with open("reward_function_test_results.json", "w") as f:
        json.dump(
            {
                "timestamp": datetime.now().isoformat(),
                "total_tests": len(all_results),
                "results": all_results,
            },
            f,
            indent=2,
        )

    print(f"\n✅ Completed testing all conditions!")
    print(f"📄 Results saved to reward_function_test_results.json")

    # Overall statistics
    if all_results:
        overall_avg = sum(r["score"] for r in all_results) / len(all_results)
        print(f"📊 Overall average score: {overall_avg:.2f}")


if __name__ == "__main__":
    print("🚀 Testing ChatGPT Reward Function with Vignettes")
    print(f"📋 Vignettes File: {VIGNETTES_FILE}")

    # Choose what to run
    print("\nChoose test mode:")
    print("1. Quick test with 5 vignettes")
    print("2. Test all conditions (full test)")

    choice = input("Enter choice (1 or 2): ").strip()

    if choice == "1":
        test_reward_function_with_vignettes()
    elif choice == "2":
        test_all_conditions()
    else:
        print("Invalid choice. Running quick test...")
        test_reward_function_with_vignettes()

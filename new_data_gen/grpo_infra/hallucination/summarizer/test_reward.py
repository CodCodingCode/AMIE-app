import requests
import json
import os
from datetime import datetime
import re

# ============================================================================
# REPLACE THESE WITH YOUR ACTUAL VALUES
# ============================================================================
ENDPOINT_URL = "url"  # Your endpoint URL from the screenshot
HF_TOKEN = "url"  # Your HuggingFace token


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

# ─── ChatGPT Reward Function ────────────────────────────────────────
from openai import OpenAI
import time
import multiprocessing
import shutil
from itertools import islice
import random

# Initialize OpenAI client
client = OpenAI(
    api_key="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"
)
model = "gpt-4o-mini"


def chatgpt_hallucination_reward(prompts, completions, **kwargs):
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
- Deduct 2 points for each hallucinated item
- Deduct 1 point for each important omitted item  
- Add 0.5 points for each accurate item
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


def test_reward_function():
    """Test the ChatGPT reward function with real examples"""

    print("🧪 Testing ChatGPT Reward Function")
    print("=" * 50)

    # Test case 1: Generate a clinical summary using your model
    test_prompt = """
Instruction: You are a clinical summarizer. Given a transcript of a doctor–patient dialogue, extract a structured clinical vignette summarizing the key symptoms, relevant history, and any diagnostic clues.
Input: I am 17. I am a female. I have had this really bad headache since yesterday that won't go away. It's on the left side of my head and feels like throbbing. Light hurts my eyes and loud noises make it worse. I threw up once this morning. My mom gets migraines too. Previous Vignette: 
Output: THINKING: 
"""

    print("🔄 Generating clinical summary with your model...")
    model_output = model_client.generate(test_prompt, max_new_tokens=400)

    print("📋 Model Output:")
    print(model_output)
    print("\n" + "-" * 50)

    # Test the reward function
    print("🔄 Testing reward function...")
    rewards = chatgpt_hallucination_reward([test_prompt], [model_output])

    print(f"🎯 Final Reward Score: {rewards[0]}")
    print("\n" + "=" * 50)

    # Test case 2: Create a deliberately hallucinated example
    print("\n🧪 Testing with deliberately hallucinated example...")

    hallucinated_example = """
THINKING: The patient is presenting with multiple concerning symptoms.
ANSWER: Chief Complaint: 17-year-old patient reports severe headache with dizziness, repeated vomiting, and extreme fatigue.
Demographics: Gender not specified.
History of Present Illness: Patient describes onset of symptoms 2 days ago with worsening headache, located bilaterally with pulsating quality. Associated with severe photophobia, phonophobia, nausea, and multiple episodes of vomiting. Patient appears lethargic and reports difficulty concentrating.
"""

    rewards2 = chatgpt_hallucination_reward([test_prompt], [hallucinated_example])
    print(f"🎯 Hallucinated Example Reward Score: {rewards2[0]}")

    # Test case 3: Create a perfect example
    print("\n🧪 Testing with accurate example...")

    accurate_example = """
THINKING: I need to extract only the facts mentioned by the patient.
ANSWER: Chief Complaint: 17-year-old female reports severe headache.
Demographics: 17-year-old female.
History of Present Illness: Patient reports headache onset yesterday, persistent and unrelenting. Headache is left-sided with throbbing quality. Associated with photophobia and phonophobia. Single episode of vomiting this morning.
Family History: Mother has history of migraines.
"""

    rewards3 = chatgpt_hallucination_reward([test_prompt], [accurate_example])
    print(f"🎯 Accurate Example Reward Score: {rewards3[0]}")

    print("\n" + "=" * 50)
    print("✅ Reward function testing complete!")
    print(f"Model Output Score: {rewards[0]}")
    print(f"Hallucinated Score: {rewards2[0]} (should be negative)")
    print(f"Accurate Score: {rewards3[0]} (should be positive)")


if __name__ == "__main__":
    print("🚀 Testing ChatGPT Reward Function")

    # Test the reward function
    test_reward_function()

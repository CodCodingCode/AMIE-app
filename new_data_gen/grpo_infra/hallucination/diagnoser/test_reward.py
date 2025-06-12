import requests
import json
import os
from datetime import datetime
import re

# ============================================================================
# REPLACE THESE WITH YOUR ACTUAL VALUES
# ============================================================================
ENDPOINT_URL = "https://glg6vtpv72vt2jad.us-east-1.aws.endpoints.huggingface.cloud"  # Your endpoint URL from the screenshot
HF_TOKEN = "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"  # Your HuggingFace token


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
model = "gpt-4.1-nano"


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
You are an expert clinical fact-checker. Your job is to compare a clinical vignette with a diagnostic reasoning response to identify any hallucinations or inaccuracies.

CLINICAL VIGNETTE (SOURCE OF TRUTH):
{clinical_vignette}

DIAGNOSTIC REASONING TO EVALUATE:
{completion}

Please analyze if the diagnostic reasoning adds any information that was NOT in the clinical vignette AND if it missed any important information that WAS in the vignette. Look for:

HALLUCINATIONS (things added that weren't in the vignette):
1. Symptoms not mentioned in the vignette
2. Demographic information that contradicts the vignette
3. Medical history not provided in the vignette
4. Timeline details not specified in the vignette
5. Severity descriptions not supported by the vignette
6. Physical exam findings not mentioned in the vignette
7. Test results or lab values not provided in the vignette

OMISSIONS (important things from vignette that diagnosis missed):
1. Key symptoms from vignette not considered in differential
2. Important demographic details that affect diagnosis
3. Relevant medical history that impacts diagnostic reasoning
4. Timeline information that narrows differential
5. Physical findings that support or rule out diagnoses

INAPPROPRIATE DIAGNOSTIC REASONING:
1. Diagnoses that don't match the clinical presentation
2. Missing common/likely diagnoses for the presentation
3. Including diagnoses without proper justification from vignette

Respond with a JSON object containing:
- "hallucinated_items": [list of specific things added that weren't in vignette]
- "omitted_items": [list of important vignette details not considered]
- "accurate_items": [list of diagnoses/reasoning correctly based on vignette]
- "score": a number from -10 to +10 (-10 = severe hallucination/poor reasoning, +10 = perfect diagnostic reasoning)

Scoring guidance:
- Deduct 3 points for each hallucinated clinical detail
- Deduct 2 points for each inappropriate diagnosis
- Deduct 1 point for each important omitted consideration
- Add 1 point for each accurate diagnosis with proper justification
- Perfect diagnostic reasoning based only on vignette information = +10

Example response:
{{"hallucinated_items": ["patient reports chest pain", "history of diabetes"], "omitted_items": ["age consideration for pancreatic cancer"], "accurate_items": ["gallstone obstruction matches jaundice", "abdominal pain fits biliary pathology"], "score": -3}}
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

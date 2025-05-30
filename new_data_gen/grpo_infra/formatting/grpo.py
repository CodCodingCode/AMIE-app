import os
import re
from typing import List
from pydantic import BaseModel
from openai import OpenAI
from trl import PPOTrainer, PPOConfig  # or GRPOTrainer/GRPOConfig
from transformers import AutoTokenizer, AutoModelForCausalLM

# Initialize OpenAI client
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])


# Define Pydantic model for structured output
class SymptomList(BaseModel):
    symptoms: List[str]


# ─── Symptom Matching Reward Function ─────────────────────────────
def extract_symptoms(disease: str) -> List[str]:
    prompt = (
        "List the 5 most common symptoms of this disease."
        "Return the symptoms in a JSON array under the key 'symptoms'.\n\n"
        f"Disease: {disease}"
    )
    response = client.chat.completions.create(
        model="gpt-4.1-nano",
        messages=[
            {"role": "system", "content": "You are a medical assistant."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.0,
        max_tokens=150,
        response_format=SymptomList,
    )
    symptom_list = response.choices[0].message.parsed
    return [symptom.strip().lower() for symptom in symptom_list.symptoms]


def symptom_matching_reward_fn(
    prompts: List[str], generations: List[str]
) -> List[float]:
    rewards = []
    for true_diagnosis, predicted_diagnosis in zip(prompts, generations):
        try:
            true_symptoms = set(extract_symptoms(true_diagnosis))
            pred_symptoms = set(extract_symptoms(predicted_diagnosis))
            matches = true_symptoms.intersection(pred_symptoms)
            score = min(1.0, 0.2 * len(matches))
        except Exception as e:
            print(f"[Error] Failed to extract symptoms: {e}")
            score = 0.0
        rewards.append(score)
    return rewards


# ─── Load base model and tokenizer ────────────────────────────────
model_name = "CodCodingCode/llama-3.1-8b-clinical"
tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=False)
model = AutoModelForCausalLM.from_pretrained(model_name, device_map="auto")

# ─── PPO/GRPO Configuration ───────────────────────────────────────
config = PPOConfig(
    model_name=model_name,
    batch_size=4,
    learning_rate=1e-5,
    ppo_epochs=1,
)

trainer = PPOTrainer(
    model=model,
    tokenizer=tokenizer,
    config=config,
    dataset=your_tokenized_dataset,  # Replace with your actual dataset
    compute_rewards=symptom_matching_reward_fn,
)

trainer.train()

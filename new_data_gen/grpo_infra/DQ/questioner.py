import os
import re
from typing import List
from pydantic import BaseModel
from openai import OpenAI
from trl import PPOTrainer, PPOConfig  # or GRPOTrainer/GRPOConfig
from transformers import AutoTokenizer, AutoModelForCausalLM

# Initialize OpenAI client
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

from typing import List, Dict
from pydantic import BaseModel


class SymptomWithThoughts(BaseModel):
    symptoms: List[str]
    thinking: List[str]


# ─── Symptom + Thinking Reward Function ─────────────────────────
def extract_symptoms(disease: str) -> SymptomWithThoughts:
    prompt = (
        "For the disease below, first list the 5 most common symptoms, "
        "then for each symptom give a short rationale (why it’s typical). "
        "Return a JSON object with two keys:\n"
        '  • "symptoms": an array of 5 symptom strings\n'
        '  • "thinking": an array of 5 strings, each explaining why the corresponding symptom is common\n\n'
        f"Disease: {disease}"
    )
    response = client.chat.completions.create(
        model="gpt-4.1-nano",
        messages=[
            {"role": "system", "content": "You are a medical assistant."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.0,
        max_tokens=300,
        response_format=SymptomWithThoughts,
    )
    return response.choices[0].message.parsed


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
    batch_size=8,
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

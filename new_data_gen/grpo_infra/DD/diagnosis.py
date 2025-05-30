import os
import re
import json
import torch
from openai import OpenAI
from pydantic import BaseModel, ValidationError
from typing import List, Dict, Optional
from datasets import Dataset
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    TrainingArguments,
    DataCollatorForLanguageModeling,
)
from trl import GRPOConfig, GRPOTrainer
import numpy as np

# ─── OpenAI client ───────────────────────────────────────────────
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

# ─── Your fixed reference for formatting (must be length 10) ─────
reference_diseases = [
    "Asthma",
    "COPD",
    "Pneumonia",
    "Bronchitis",
    "Tuberculosis",
    "Emphysema",
    "Cystic fibrosis",
    "Lung cancer",
    "Pulmonary edema",
    "Sarcoidosis",
]


# ─── Pydantic models ─────────────────────────────────────────────
class DiseaseCheck(BaseModel):
    count: int
    diseases: List[str]
    reasoning: str


def parse_disease_check(resp_text: str) -> DiseaseCheck:
    try:
        return DiseaseCheck.parse_raw(resp_text)
    except ValidationError:
        return DiseaseCheck(count=0, diseases=[], reasoning="invalid response")


class ReferenceList(BaseModel):
    diseases: List[str]


# ─── Prompt templates ────────────────────────────────────────────
DIAGNOSIS_PROMPT_TEMPLATE = """You are a board-certified clinician. Given the patient vignette below, provide the 10 most likely diagnoses in JSON format.

Return ONLY a JSON object with the following structure:
{
    "count": 10,
    "diseases": ["diagnosis1", "diagnosis2", ..., "diagnosis10"],
    "reasoning": "brief explanation of your diagnostic reasoning"
}

Patient vignette:
{vignette}"""

DIAGNOSIS_LIST_PROMPT = """
You are a board-certified clinician.
Given the patient vignette below, list the 10 most likely diagnoses.
Return ONLY a JSON object with key "diseases" mapping to an array of 10 diagnosis strings.
Patient vignette:
{vignette}
"""


# ─── Original reward function ────────────────────────────────────
def combined_openai_reward_fn(
    prompts: List[str], generations: List[str]
) -> List[List[float]]:
    all_rewards: List[List[float]] = []
    expected_count = len(reference_diseases)
    ref_lower = [d.lower() for d in reference_diseases]

    for vignette, gen_json in zip(prompts, generations):
        # ── 1) Formatting check ──────────────────────────────────
        dc = parse_disease_check(gen_json)
        gen_lower = [d.strip().lower() for d in dc.diseases]

        # penalty if not exactly 10
        factor = max(0.0, min(1.0, dc.count / expected_count))

        # exact‐match per index
        fmt_pairs = list(zip(ref_lower, gen_lower))
        f_rewards = [1.0 if ref == gen else 0.0 for ref, gen in fmt_pairs]
        if len(f_rewards) < expected_count:
            f_rewards += [0.0] * (expected_count - len(f_rewards))
        else:
            f_rewards = f_rewards[:expected_count]

        # apply count penalty
        f_rewards = [r * factor for r in f_rewards]

        # ── 2) Diagnostic accuracy check ────────────────────────
        chat_resp = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a board-certified clinician."},
                {
                    "role": "user",
                    "content": DIAGNOSIS_LIST_PROMPT.format(vignette=vignette),
                },
            ],
            temperature=0.0,
            max_tokens=200,
        )

        try:
            ref_list = ReferenceList.parse_raw(chat_resp.choices[0].message.content)
            ref_sample_lower = [d.strip().lower() for d in ref_list.diseases]
        except ValidationError:
            ref_sample_lower = []

        # compare ChatGPT's list to the model's
        diag_pairs = list(zip(ref_sample_lower, gen_lower))
        d_rewards = [1.0 if ref == gen else 0.0 for ref, gen in diag_pairs]
        if len(d_rewards) < expected_count:
            d_rewards += [0.0] * (expected_count - len(d_rewards))
        else:
            d_rewards = d_rewards[:expected_count]

        # ── 3) Combine 50/50 ───────────────────────────────────
        combined = [0.5 * f + 0.5 * d for f, d in zip(f_rewards, d_rewards)]
        all_rewards.append(combined)

    return all_rewards


# ─── GRPO-compatible reward function ─────────────────────────────
def grpo_reward_function(prompts: List[str], completions: List[str]) -> List[float]:
    """
    GRPO-compatible reward function that returns a single scalar reward per completion.
    Averages the per-position rewards from the original function.
    """
    position_rewards = combined_openai_reward_fn(prompts, completions)

    # Average across all positions to get single scalar reward per completion
    scalar_rewards = [np.mean(rewards) for rewards in position_rewards]
    return scalar_rewards


# ─── Dataset preparation ─────────────────────────────────────────
def prepare_medical_dataset(vignettes: List[str]) -> Dataset:
    """
    Prepare dataset for GRPO training.
    Each vignette becomes a prompt for diagnosis generation.
    """
    formatted_prompts = [
        DIAGNOSIS_PROMPT_TEMPLATE.format(vignette=vignette) for vignette in vignettes
    ]

    dataset_dict = {
        "prompt": formatted_prompts,
        "vignette": vignettes,  # Keep original for reference
    }

    return Dataset.from_dict(dataset_dict)


# ─── GRPO Training Class ─────────────────────────────────────────
class MedicalDiagnosisGRPOTrainer:
    def __init__(
        self,
        model_name: str = "CodCodingCode/llama-3.1-8b-clinical-v1.1",  # Or any suitable medical LLM
        output_dir: str = "./grpo_medical_model",
        learning_rate: float = 1e-5,
        batch_size: int = 4,
        gradient_accumulation_steps: int = 4,
        num_train_epochs: int = 3,
        group_size: int = 4,  # GRPO group size
        max_length: int = 512,
    ):
        self.model_name = model_name
        self.output_dir = output_dir
        self.max_length = max_length

        # Load model and tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto" if torch.cuda.is_available() else None,
        )

        # GRPO Configuration
        self.grpo_config = GRPOConfig(
            learning_rate=learning_rate,
            batch_size=batch_size,
            gradient_accumulation_steps=gradient_accumulation_steps,
            num_train_epochs=num_train_epochs,
            group_size=group_size,
            max_length=max_length,
            output_dir=output_dir,
            logging_steps=10,
            save_steps=500,
            eval_steps=100,
            warmup_steps=100,
            remove_unused_columns=False,
        )

    def train(self, train_dataset: Dataset, eval_dataset: Optional[Dataset] = None):
        """
        Train the model using GRPO with the medical diagnosis reward function.
        """
        # Initialize GRPO trainer
        trainer = GRPOTrainer(
            model=self.model,
            args=self.grpo_config,
            train_dataset=train_dataset,
            eval_dataset=eval_dataset,
            tokenizer=self.tokenizer,
            reward_function=grpo_reward_function,
        )

        # Start training
        print("Starting GRPO training...")
        trainer.train()

        # Save the final model
        trainer.save_model()
        self.tokenizer.save_pretrained(self.output_dir)

        print(f"Training completed! Model saved to {self.output_dir}")

        return trainer

    def generate_diagnosis(self, vignette: str, max_new_tokens: int = 200) -> str:
        """
        Generate diagnosis for a given vignette using the trained model.
        """
        prompt = DIAGNOSIS_PROMPT_TEMPLATE.format(vignette=vignette)

        inputs = self.tokenizer(
            prompt, return_tensors="pt", truncation=True, max_length=self.max_length
        )

        if torch.cuda.is_available():
            inputs = {k: v.cuda() for k, v in inputs.items()}

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=0.7,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
            )

        # Decode only the generated part
        generated_text = self.tokenizer.decode(
            outputs[0][inputs["input_ids"].shape[1] :], skip_special_tokens=True
        )

        return generated_text.strip()


# ─── Example usage ───────────────────────────────────────────────
def main():
    # Example medical vignettes for training
    sample_vignettes = [
        "A 45-year-old male smoker presents with chronic cough, dyspnea on exertion, and wheezing. Chest X-ray shows hyperinflation.",
        "A 28-year-old female presents with acute onset chest pain, fever, and productive cough with yellow sputum.",
        "A 65-year-old male with a history of smoking presents with weight loss, hemoptysis, and a mass on chest CT.",
        "A 35-year-old female presents with episodic wheezing, chest tightness, and shortness of breath triggered by exercise.",
        # Add more vignettes for robust training...
    ]

    # Prepare dataset
    train_dataset = prepare_medical_dataset(sample_vignettes)

    # Initialize trainer
    trainer = MedicalDiagnosisGRPOTrainer(
        model_name="microsoft/DialoGPT-medium",
        output_dir="./medical_grpo_model",
        learning_rate=1e-5,
        batch_size=2,
        num_train_epochs=3,
        group_size=4,
    )

    # Train the model
    grpo_trainer = trainer.train(train_dataset)

    # Test generation
    test_vignette = "A 50-year-old smoker with chronic shortness of breath and morning cough with clear sputum."
    diagnosis = trainer.generate_diagnosis(test_vignette)
    print(f"Generated diagnosis: {diagnosis}")


if __name__ == "__main__":
    main()

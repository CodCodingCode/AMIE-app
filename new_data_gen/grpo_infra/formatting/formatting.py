import os
import re

from datasets import load_dataset
from transformers import AutoTokenizer, AutoModelForCausalLM
from trl import GRPOConfig, GRPOTrainer

# 1. Load base model & tokenizer
model_name = "CodCodingCode/llama-3.1-8b-clinical"
tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=False)
model     = AutoModelForCausalLM.from_pretrained(model_name, device_map="auto")

# 2. Load & filter the dataset
ds = load_dataset("CodCodingCode/clinical-conversations", split="train")
ds = ds.filter(lambda ex: ex["instruction"] != "You are simulating a real patient in conversation with their doctor.")

# 3. Build prompt‐only dataset
def make_prompt(ex):
    instr = ex["instruction"].strip()
    inp   = ex.get("input", "").strip()
    full  = instr + ("\n" + inp if inp else "")
    return {"prompt": full}

prompt_ds = ds.map(make_prompt, remove_columns=ds.column_names)

# 4. Tokenize
tokenized = prompt_ds.map(
    lambda ex: tokenizer(
        ex["prompt"],
        truncation=True,
        padding="max_length",
        max_length=512
    ),
    batched=True,
    remove_columns=["prompt"],
)

# 5. Define your THINKING/ANSWER reward fn
def thinking_answer_reward(prompts, completions, **kwargs):
    rewards = []
    for text in completions:
        t = text.strip().lower()
        ok = (
            t.count("thinking:") == 1 and
            t.count("answer:")   == 1 and
            t.find("thinking:") < t.find("answer:")
        )
        rewards.append(1.0 if ok else 0.0)
    return rewards

# 6. Configure GRPO
config = GRPOConfig(
    model_name=model_name,
    output_dir="llama-3.1-8b-clinical-think-answer",
    batch_size=4,
    group_size=8,
    learning_rate=1e-5,
    # some versions expect ppo_epochs rather than num_epochs:
    ppo_epochs=3,
    kl_coef=0.1,
)

# 7. Instantiate & train
trainer = GRPOTrainer(
    model=model,
    tokenizer=tokenizer,
    config=config,                # <-- not args=
    train_dataset=tokenized,      # <-- fully tokenized
    reward_funcs=thinking_answer_reward,  # or compute_rewards=…
)

if __name__ == "__main__":
    trainer.train()
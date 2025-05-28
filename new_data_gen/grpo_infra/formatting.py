import os
import re

from transformers import AutoTokenizer, AutoModelForCausalLM
from datasets import load_dataset
from trl import GRPOConfig, GRPOTrainer

# ─── 1. Load base model & tokenizer ────────────────────────────
model_name = "CodCodingCode/llama-3.1-8b-clinical"
tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=False)
model = AutoModelForCausalLM.from_pretrained(model_name, device_map="auto")

# ─── 2. Load & filter the Clinical Conversations dataset ────────
ds = load_dataset("CodCodingCode/clinical-conversations", split="train")

# Drop the one unwanted instruction
unwanted = "You are simulating a real patient in conversation with their doctor."
filtered = ds.filter(lambda ex: ex["instruction"] != unwanted)


# ─── 3. Build prompt-only dataset ──────────────────────────────
def make_prompt(ex):
    instr = ex["instruction"].strip()
    inp = ex["input"].strip()
    # put patient input on its own line if present
    full = instr + ("\n" + inp if inp else "")
    return {"prompt": full}


prompt_ds = filtered.map(
    make_prompt,
    remove_columns=[c for c in filtered.column_names if c not in ("prompt",)],
)

print(f"Total examples after drop: {len(prompt_ds)}")
print("Example prompt:", prompt_ds[0]["prompt"])


# ─── 4. Define THINKING/ANSWER reward function ────────────────
def thinking_answer_reward(prompts, completions, **kwargs):
    rewards = []
    for completion in completions:
        text = completion.strip().lower()
        thinking_count = text.count("thinking:")
        answer_count = text.count("answer:")
        thinking_pos = text.find("thinking:")
        answer_pos = text.find("answer:")

        if (
            thinking_count == 1
            and answer_count == 1
            and thinking_pos != -1
            and answer_pos != -1
            and thinking_pos < answer_pos
        ):
            rewards.append(1.0)
        else:
            rewards.append(0.0)
    return rewards


# ─── 5. Configure & launch GRPO training ───────────────────────
config = GRPOConfig(
    output_dir="llama-3.1-8b-clinical-think-answer",
    batch_size=4,
    group_size=8,
    learning_rate=1e-5,
    num_epochs=3,
    logging_steps=20,
    save_steps=500,
    kl_coef=0.1,
)

trainer = GRPOTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=prompt_ds,
    reward_funcs=thinking_answer_reward,
    args=config,
)

trainer.train()

# This file is to improve the quality of the diagnosis model through GRPO

import os
import re
from openai import OpenAI
from trl import PPOTrainer, PPOConfig  # or GRPOTrainer/GRPOConfig
from transformers import AutoTokenizer, AutoModelForCausalLM

# Your normal ChatGPT client
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

# ─── Reward function using ChatGPT via `client` ────────────────
def openai_reward_fn(prompts: list[str], generations: list[str]) -> list[float]:
    rewards = []
    for instruction, response in zip(prompts, generations):
        # build the evaluation prompt
        eval_prompt = (
            "You are a strict grader.  "
            "On a scale from 0.0 to 1.0, how well does this response "
            "follow the instruction?  Reply with a single number.\n\n"
            f"Instruction:\n{instruction}\n\n"
            f"Response:\n{response}\n\n"
            "Score:"
        )
        # call your OpenAI client
        chat_resp = client.chat.completions.create(
            model="gpt-4.1-nano",
            messages=[
                {"role": "system", "content": "You are a strict numeric grader."},
                {"role": "user",   "content": eval_prompt},
            ],
            temperature=0.0,
            max_tokens=4,
        )
        text = chat_resp.choices[0].message.content.strip()
        # parse float, fallback to regex
        try:
            score = float(text)
        except ValueError:
            m = re.search(r"0\.\d+|1\.0|1", text)
            score = float(m.group(0)) if m else 0.0
        rewards.append(max(0.0, min(1.0, score)))
    return rewards

# ─── Load your base model & tokenizer ──────────────────────────
model_name = "CodCodingCode/llama-3.1-8b-clinical"
tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=False)
model     = AutoModelForCausalLM.from_pretrained(model_name, device_map="auto")

# ─── Configure and launch your PPO/GRPO trainer ────────────────
config = PPOConfig(
    model_name=model_name,
    batch_size=4,
    learning_rate=1e-5,
    ppo_epochs=1,    # for GRPO use group_size instead
)

trainer = PPOTrainer(
    model=model,
    tokenizer=tokenizer,
    config=config,
    dataset=your_tokenized_dataset,
    compute_rewards=openai_reward_fn,  # your ChatGPT-based reward
)

trainer.train()
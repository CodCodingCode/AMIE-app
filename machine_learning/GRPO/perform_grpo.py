import json
from datasets import load_dataset, Dataset
from transformers import AutoTokenizer
from trl import GRPOTrainer, GRPOConfig

# ────────────────────────────────────────────────────────────────────────────────
# 1. Load and format your data
# ────────────────────────────────────────────────────────────────────────────────
def format_prompt(example):
    instr = example["instruction"].strip()
    inp = example["input"].strip()
    return f"### Instruction:\n{instr}\n\n### Input:\n{inp}\n\n### Response:"

# Load your dataset (from a JSONL file)
raw_data = []
with open("your_dataset.jsonl", "r") as f:
    for line in f:
        item = json.loads(line)
        if "instruction" in item and "input" in item:
            raw_data.append({"prompt": format_prompt(item)})

dataset = Dataset.from_list(raw_data)

# ────────────────────────────────────────────────────────────────────────────────
# 2. Set up tokenizer and model path
# ────────────────────────────────────────────────────────────────────────────────
sft_model_path = "./ppo_ready_output"
tokenizer = AutoTokenizer.from_pretrained(sft_model_path, use_fast=False)
tokenizer.pad_token = tokenizer.eos_token

# ────────────────────────────────────────────────────────────────────────────────
# 3. Define a reward function (example: reward longer completions)
# ────────────────────────────────────────────────────────────────────────────────
def reward_func(completions, **kwargs):
    return [float(len(c)) for c in completions]

# ────────────────────────────────────────────────────────────────────────────────
# 4. Set up GRPOConfig
# ────────────────────────────────────────────────────────────────────────────────
config = GRPOConfig(
    output_dir="./grpo_output",
    per_device_train_batch_size=1,
    gradient_accumulation_steps=1,
    num_train_epochs=1,
    logging_steps=10,
    save_strategy="epoch",
    learning_rate=5e-6,
    bf16=True,
    gradient_checkpointing=True,
    max_completion_length=128,
    num_generations=2,
    loss_type="dr_grpo"
)

# ────────────────────────────────────────────────────────────────────────────────
# 5. Train using GRPOTrainer
# ────────────────────────────────────────────────────────────────────────────────
trainer = GRPOTrainer(
    model=sft_model_path,
    tokenizer=tokenizer,
    args=config,
    reward_funcs=reward_func,
    train_dataset=dataset,
)

trainer.train()
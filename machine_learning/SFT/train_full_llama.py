#!/usr/bin/env python3

import torch
from datasets import load_dataset
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    Trainer,
    TrainingArguments,
)

# 1) Load and inspect data
raw_ds = load_dataset("CodCodingCode/clinical-conversations", split="train")
print(raw_ds.features, raw_ds[0])

# 2) Alpaca-style prompt formatter
def format_fn(example):
    return {
        "text": (
            f"### Instruction:\n{example['instruction']}\n\n"
            f"### Input:\n{example['input']}\n\n"
            f"### Response:\n{example['output']}"
        )
    }

ds = raw_ds.map(format_fn, remove_columns=raw_ds.column_names)

# 3) Tokenizer + base model in BF16
model_name = "meta-llama/Llama-3.1-8B"

tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=False)
# Set pad token for batching
tokenizer.pad_token = tokenizer.eos_token

model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype=torch.bfloat16,
    device_map="auto"
)
# Align pad_token_id
model.config.pad_token_id = tokenizer.eos_token_id

# 4) Tokenize and prepare labels for causal LM
def tokenize_fn(examples):
    tokens = tokenizer(
        examples["text"],
        padding=True,
        truncation=True,
        max_length=2048
    )
    # Use input_ids also as labels for full-model fine-tuning
    tokens["labels"] = tokens.input_ids.copy()
    return tokens

train_ds = ds.map(tokenize_fn, batched=True, remove_columns=["text"])

# 5) Training configuration for full fine-tuning
training_args = TrainingArguments(
    output_dir="outputs/full_finetune",
    per_device_train_batch_size=1,
    gradient_accumulation_steps=8,
    max_steps=45000,                  # adjust as needed for your epochs
    learning_rate=2e-5,             # lower LR for full-model fine-tuning
    optim="adamw_torch",
    bf16=True,                      # GH200 supports BF16
    fp16=False,
    logging_steps=10,
    save_strategy="steps",
    save_steps=500,
    save_total_limit=2,
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_ds,
    tokenizer=tokenizer,
)

# 6) Fine-tune all model weights
trainer.train()

# 7) Save final model
trainer.save_model("outputs/full_finetune")
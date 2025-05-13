# h100_fp16_peft_then_grpo.py

import os
import gc
import json
import torch
from datasets import Dataset
from transformers import (
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling,
    GenerationConfig,
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from trl import (
    AutoModelForCausalLMWithValueHead,
    PPOConfig,
    PPOTrainer,
)

# ────────────────────────────────────────────────────────────────────────────────
# 1) SFT LoRA on a value‐head model
# ────────────────────────────────────────────────────────────────────────────────
gc.collect(); torch.cuda.empty_cache()

model_name = "aaditya/Llama3-OpenBioLLM-8B"
tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=False)
if tokenizer.pad_token_id is None:
    tokenizer.pad_token_id = tokenizer.eos_token_id

# 1a) load value‐head LM
sft_model = AutoModelForCausalLMWithValueHead.from_pretrained(
    model_name, torch_dtype=torch.float16, device_map="auto"
)

# 1b) prepare + attach LoRA
sft_model = prepare_model_for_kbit_training(sft_model)
lora_cfg = LoraConfig(
    r=16,
    lora_alpha=32,
    target_modules=["q_proj","k_proj","v_proj","o_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM",
)
sft_model = get_peft_model(sft_model, lora_cfg)

# ─── NEW ───
# memory savings
sft_model.gradient_checkpointing_enable()
sft_model.config.use_cache = False
# ──────────

sft_model.print_trainable_parameters()

# 1c) manual JSONL load + skip bad
records = []
with open("combined_dataset_clean.jsonl","r") as f:
    for i,line in enumerate(f,1):
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue
print(f"✅ Loaded {len(records)} records")

ds = Dataset.from_list(records)

# format, skip empty outputs
def format_ex(x):
    out = x.get("output")
    if not out:
        return {"text": ""}
    return {"text": f"Diagnosis: {out.strip()}\n"}
ds = ds.map(format_ex, batched=False)
ds = ds.filter(lambda x: x["text"]!=="")          # drop empties

# tokenize + set labels
def tok_fn(x):
    toks = tokenizer(x["text"], truncation=True, max_length=64)
    toks["labels"] = toks["input_ids"].copy()
    return toks

tokenized = ds.map(tok_fn, batched=True, remove_columns=["output","text"])


# ────────────────────────────────────────────────────────────────────────────────
# custom Trainer to extract scalar loss
class SFTTrainer(Trainer):
    def compute_loss(self, model, inputs, return_outputs=False):
        labels = inputs.pop("labels")
        outputs = model(**inputs, labels=labels)
        loss = outputs.loss if hasattr(outputs, "loss") else outputs[0]
        return (loss, outputs) if return_outputs else loss


# 1d) train SFT
sft_args = TrainingArguments(
    output_dir="./sft_output",
    per_device_train_batch_size=1,
    gradient_accumulation_steps=1,
    gradient_checkpointing=True,
    num_train_epochs=1,
    save_strategy="epoch",
    fp16=True,
)
collator = DataCollatorForLanguageModeling(tokenizer, mlm=False)
sft_trainer = SFTTrainer(
    model=sft_model,
    args=sft_args,
    train_dataset=tokenized,
    data_collator=collator,
)
sft_trainer.train()
sft_trainer.save_model("./sft_output")
tokenizer.save_pretrained("./sft_output")

del sft_trainer, ds, tokenized, collator
gc.collect(); torch.cuda.empty_cache()


# ────────────────────────────────────────────────────────────────────────────────
# 2) GRPO on your freshly SFT’d model
# ────────────────────────────────────────────────────────────────────────────────

policy = AutoModelForCausalLMWithValueHead.from_pretrained(
    "./sft_output", torch_dtype=torch.float16, device_map="auto"
)
policy.generation_config = GenerationConfig(**policy.config.to_dict())

ref = AutoModelForCausalLMWithValueHead.from_pretrained(
    model_name, torch_dtype=torch.float16, device_map="cpu"
)
ref.generation_config = policy.generation_config

reward_model = AutoModelForCausalLMWithValueHead.from_pretrained(
    model_name, torch_dtype=torch.float16, device_map="cpu"
).eval()
reward_tok = tokenizer

def get_reward(q, r):
    with torch.no_grad():
        toks = reward_tok(q+r, truncation=True, max_length=1024, return_tensors="pt").to("cpu")
        return float(reward_model(**toks).logits[:, -1].mean())

ppo_trainer = PPOTrainer(
    PPOConfig(learning_rate=1e-5, batch_size=1, mini_batch_size=1),
    tokenizer, policy, ref, reward_model,
    ["Patient has a fever and cough, what question do you ask?"],
    policy,
)

for q in ppo_trainer.prompts:
    ids = tokenizer(q, return_tensors="pt").input_ids.to(policy.device)
    gen = policy.generate(ids, max_new_tokens=64, pad_token_id=tokenizer.pad_token_id)
    resp = tokenizer.decode(gen[0][ids.shape[-1]:], skip_special_tokens=True)
    r = get_reward(q, resp)
    print(f"[REWARD={r:.4f}] {resp}")
    ppo_trainer.step([q],[resp],[r])

policy.save_pretrained("./grpo_output")
tokenizer.save_pretrained("./grpo_output")



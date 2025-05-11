# h100_fp16_peft_then_grpo.py

import os
import gc
import torch
from datasets import load_dataset
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

# 1) ----------------------------------------------------------------------------
# SFT LoRA on a value-head model
# -----------------------------------------------------------------------------
gc.collect()
torch.cuda.empty_cache()

model_name = "aaditya/Llama3-OpenBioLLM-8B"
tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=False)
if tokenizer.pad_token_id is None:
    tokenizer.pad_token_id = tokenizer.eos_token_id

# 1a) load value-head LM
sft_model = AutoModelForCausalLMWithValueHead.from_pretrained(
    model_name, torch_dtype=torch.float16, device_map="auto"
)
# 1b) prepare + attach LoRA
sft_model = prepare_model_for_kbit_training(sft_model)
lora_cfg = LoraConfig(
    r=16, lora_alpha=32, target_modules=["q_proj","k_proj","v_proj","o_proj"],
    lora_dropout=0.05, bias="none", task_type="CAUSAL_LM"
)
sft_model = get_peft_model(sft_model, lora_cfg)
sft_model.print_trainable_parameters()

# 1c) dataset & tokenization
raw = load_dataset("json", data_files="combined_dataset.jsonl")["train"]
def format_ex(x):
    return {"text": f"Diagnosis: {x['output'].strip()}\n"}
ds = raw.map(format_ex)
def tok_fn(x):
    return tokenizer(x["text"], truncation=True, max_length=64)
tokenized = ds.map(tok_fn, batched=True, remove_columns=["output"])

# 1d) SFT Trainer
sft_args = TrainingArguments(
    output_dir="./sft_output",
    per_device_train_batch_size=2,
    gradient_accumulation_steps=2,
    num_train_epochs=1,
    save_strategy="epoch",
    fp16=True,
)
collator = DataCollatorForLanguageModeling(tokenizer, mlm=False)
sft_trainer = Trainer(
    model=sft_model,
    args=sft_args,
    train_dataset=tokenized,
    data_collator=collator,
)
sft_trainer.train()
sft_trainer.save_model("./sft_output")
tokenizer.save_pretrained("./sft_output")

# Free up all GPU memory before RL
del sft_trainer, raw, ds, tokenized, collator
gc.collect(); torch.cuda.empty_cache()


# 2) ----------------------------------------------------------------------------
# GRPO on your freshly SFT’d model
# -----------------------------------------------------------------------------

# 2a) reload policy + value-head from SFT output
policy = AutoModelForCausalLMWithValueHead.from_pretrained(
    "./sft_output", torch_dtype=torch.float16, device_map="auto"
)
# inject minimal generation_config so .generate() works
policy.generation_config = GenerationConfig(**policy.config.to_dict())

# 2b) frozen reference (same base, no LoRA)
ref = AutoModelForCausalLMWithValueHead.from_pretrained(
    model_name, torch_dtype=torch.float16, device_map="cpu"
)
ref.generation_config = policy.generation_config

# 2c) reward model (example: same as your SFT LM, but could be any)
reward_model = AutoModelForCausalLMWithValueHead.from_pretrained(
    model_name, torch_dtype=torch.float16, device_map="cpu"
).eval()
reward_tok = tokenizer

def get_reward(query, response):
    with torch.no_grad():
        toks = reward_tok(query + response, return_tensors="pt", truncation=True, max_length=1024).to("cpu")
        logits = reward_model(**toks).logits
        return float(logits[:, -1].mean())

# 2d) PPOTrainer for GRPO
rl_prompts = [ "Patient has a fever and cough, what question do you ask?" ]  # replace with your real prompts
ppo_cfg = PPOConfig(
    learning_rate=1e-5,
    batch_size=1,
    mini_batch_size=1,
)

ppo_trainer = PPOTrainer(
    ppo_cfg,
    tokenizer,
    policy,
    ref,
    reward_model,
    rl_prompts,
    policy,
)

# 2e) GRPO loop
for q in rl_prompts:
    input_ids = tokenizer(q, return_tensors="pt").input_ids.to(policy.device)
    gen_ids    = policy.generate(input_ids, max_new_tokens=64, pad_token_id=tokenizer.pad_token_id)
    resp       = tokenizer.decode(gen_ids[0][input_ids.shape[-1]:], skip_special_tokens=True)
    r          = get_reward(q, resp)
    print(f"[REWARD={r:.4f}] {resp}")
    ppo_trainer.step([q], [resp], [r])

# 2f) save final policy
policy.save_pretrained("./grpo_output")
tokenizer.save_pretrained("./grpo_output")
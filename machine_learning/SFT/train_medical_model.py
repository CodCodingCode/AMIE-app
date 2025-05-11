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
    BitsAndBytesConfig,
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from trl import AutoModelForCausalLMWithValueHead

# ────────────────────────────────────────────────────────────────────────────────
# 1) Memory cleanup & GPU check
# ────────────────────────────────────────────────────────────────────────────────
gc.collect()
torch.cuda.empty_cache()
if not torch.cuda.is_available():
    print("No GPU detected, exiting.")
    exit()
print(f"CUDA available: {torch.cuda.get_device_name(0)}")

# ────────────────────────────────────────────────────────────────────────────────
# 2) Load & prepare model for LoRA + Value Head + 4-bit quantization
# ────────────────────────────────────────────────────────────────────────────────
model_name = "aaditya/Llama3-OpenBioLLM-8B"
print(f"Loading value-headed model in 4-bit for PPO compatibility: {model_name}")

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_use_double_quant=True,
    bnb_4bit_compute_dtype=torch.float16,
)

model = AutoModelForCausalLMWithValueHead.from_pretrained(
    model_name,
    quantization_config=bnb_config,
    device_map="auto",
)

model = prepare_model_for_kbit_training(model)
lora_cfg = LoraConfig(
    r=16,
    lora_alpha=32,
    target_modules=["q_proj","k_proj","v_proj","o_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM",
)
model = get_peft_model(model, lora_cfg)

model.gradient_checkpointing_enable()
model.config.use_cache = False

model.print_trainable_parameters()
model.generation_config = GenerationConfig(**model.config.to_dict())

# ────────────────────────────────────────────────────────────────────────────────
# 3) Tokenizer
# ────────────────────────────────────────────────────────────────────────────────
tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=False)
if tokenizer.pad_token_id is None:
    tokenizer.pad_token_id = tokenizer.eos_token_id

# ────────────────────────────────────────────────────────────────────────────────
# 4) Load, clean & preprocess your JSONL
# ────────────────────────────────────────────────────────────────────────────────
records = []
with open("combined_dataset_clean.jsonl","r") as f:
    for i, line in enumerate(f, start=1):
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            print(f"⚠️  Skipping malformed JSON at line {i}")
            continue
        out = rec.get("output")
        if not out:
            continue
        records.append({"text": f"Diagnosis: {out.strip()}\n"})

print(f"✅ Loaded {len(records)} valid examples.")

ds = Dataset.from_list(records)

def tokenize_fn(ex):
    tokens = tokenizer(
        ex["text"],
        truncation=True,
        padding="max_length",
        max_length=64,
    )
    tokens["labels"] = tokens["input_ids"].copy()
    return tokens

tokenized = ds.map(
    tokenize_fn,
    batched=False,
    remove_columns=["text"],
)

# ────────────────────────────────────────────────────────────────────────────────
# 5) Custom Trainer (accepts extra kwargs in compute_loss)
# ────────────────────────────────────────────────────────────────────────────────
from torch.nn import CrossEntropyLoss

class SFTTrainer(Trainer):
    def compute_loss(self, model, inputs, return_outputs=False, **kwargs):
        labels = inputs.pop("labels")
        outputs = model.pretrained_model(**inputs, return_dict=True)
        logits = outputs.logits

        # shift so that tokens < n predict n
        shift_logits = logits[..., :-1, :].contiguous()
        shift_labels = labels[..., 1:].contiguous()

        # figure out a safe ignore_index
        pad_id = model.config.pad_token_id
        if pad_id is None:
            pad_id = -100

        loss_fct = CrossEntropyLoss(ignore_index=pad_id)
        loss = loss_fct(
            shift_logits.view(-1, shift_logits.size(-1)),
            shift_labels.view(-1),
        )

        return (loss, outputs) if return_outputs else loss

# ────────────────────────────────────────────────────────────────────────────────
# 6) Training setup
# ────────────────────────────────────────────────────────────────────────────────
training_args = TrainingArguments(
    output_dir="./ppo_ready_output",
    per_device_train_batch_size=1,
    gradient_accumulation_steps=1,
    gradient_checkpointing=True,
    num_train_epochs=1,
    save_strategy="epoch",
    fp16=True,
)

data_collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)

trainer = SFTTrainer(
    model=model,
    args=training_args,
    train_dataset=tokenized,
    data_collator=data_collator,
)

print("Starting fine-tuning with LoRA in 4-bit…")
trainer.train()

# ────────────────────────────────────────────────────────────────────────────────
# 7) Save the PPO-ready model & tokenizer
# ────────────────────────────────────────────────────────────────────────────────
model.save_pretrained("./ppo_ready_output")
tokenizer.save_pretrained("./ppo_ready_output")
print("✅ Model with value head + LoRA saved and ready for PPO.") 
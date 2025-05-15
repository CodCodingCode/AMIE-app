import os

# ────────── 0. SYNCHRONOUS CUDA ERRORS & DISABLE DYNAMO ──────────
os.environ["CUDA_LAUNCH_BLOCKING"] = "1"
os.environ["TORCH_USE_CUDA_DSA"] = "1"
import torch._dynamo

torch._dynamo.disable()

import gc
import json
import torch
import torch.nn as nn
from datasets import Dataset
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling,
    BitsAndBytesConfig,
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training

# ────────── 1. GPU CHECK + CLEANUP ──────────
gc.collect()
torch.cuda.empty_cache()
if not torch.cuda.is_available():
    raise SystemExit("No GPU detected.")
print(f"✅ CUDA: {torch.cuda.get_device_name(0)}")

# ────────── 2. LOAD MODEL + TOKENIZER (4-bit + LoRA) ──────────
model_name = "deepseek-ai/DeepSeek-V2-Lite"
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_use_double_quant=True,
    bnb_4bit_compute_dtype=torch.bfloat16,  # bf16 on A100
)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    quantization_config=bnb_config,
    device_map="auto",
    trust_remote_code=True,
)
tokenizer = AutoTokenizer.from_pretrained(
    model_name,
    use_fast=True,
    trust_remote_code=True,
)
tokenizer.pad_token_id = tokenizer.pad_token_id or tokenizer.eos_token_id

model = prepare_model_for_kbit_training(model)
lora_cfg = LoraConfig(
    r=16,
    lora_alpha=32,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM",
)
model = get_peft_model(model, lora_cfg)
model.config.use_cache = False
model.resize_token_embeddings(len(tokenizer))
model.print_trainable_parameters()

# ────────── 3. LOAD INSTRUCTION DATA ──────────
records = []
with open("combined_dataset_clean.jsonl", "r") as f:
    for line in f:
        rec = json.loads(line)
        instr, inp, out = (
            rec.get("instruction", "").strip(),
            rec.get("input", "").strip(),
            rec.get("output", "").strip(),
        )
        if not (instr and out):
            continue
        prompt = f"{instr}\n\n{inp}" if inp else instr
        records.append({"text": f"{prompt}\n\n### Response:\n{out}"})
print(f"✅ Loaded {len(records)} examples.")
ds = Dataset.from_list(records)


# ────────── 4. TOKENIZATION (batched + multiproc) ──────────
def tokenize_fn(batch):
    toks = tokenizer(
        batch["text"],
        truncation=True,
        padding="max_length",
        max_length=512,  # shorter context
    )
    toks["labels"] = toks["input_ids"].copy()
    return toks


tokenized = ds.map(
    tokenize_fn,
    batched=True,
    num_proc=4,
    remove_columns=["text"],
)


# ────────── 5. CUSTOM TRAINER ──────────
class SFTTrainer(Trainer):
    def compute_loss(self, model, inputs, return_outputs=False, **kwargs):
        labels = inputs.pop("labels")
        labels = torch.where(labels == tokenizer.pad_token_id, -100, labels)
        outputs = model(**inputs, return_dict=True)
        shift_logits = outputs.logits[..., :-1, :].contiguous()
        shift_labels = labels[..., 1:].contiguous()
        loss = nn.CrossEntropyLoss(ignore_index=-100)(
            shift_logits.view(-1, shift_logits.size(-1)),
            shift_labels.view(-1),
        )
        return (loss, outputs) if return_outputs else loss


# ────────── 6. TRAINING CONFIG (speed‐focused) ──────────
training_args = TrainingArguments(
    output_dir="./sft_output",
    per_device_train_batch_size=8,  # bigger micro‐batch
    gradient_accumulation_steps=1,
    gradient_checkpointing=False,
    bf16=True,  # leverage bf16 on A100
    fp16=False,
    num_train_epochs=1,
    max_steps=3600,  # cap to ~3.6k steps (~12h)
    logging_steps=200,
    save_strategy="no",
    dataloader_num_workers=4,
    optim="adamw_torch",
)

# ────────── 7. START TRAINING ──────────
data_collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)
trainer = SFTTrainer(
    model=model,
    args=training_args,
    train_dataset=tokenized,
    data_collator=data_collator,
)

print("🚀 Training begins…")
trainer.train()

# ────────── 8. SAVE MODEL ──────────
model.save_pretrained("./sft_output")
tokenizer.save_pretrained("./sft_output")
print("✅ Model saved to ./sft_output")



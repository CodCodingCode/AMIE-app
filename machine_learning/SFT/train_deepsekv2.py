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
    BitsAndBytesConfig,
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from transformers import AutoModelForCausalLM
from torch.nn import CrossEntropyLoss

# ────────── 1. GPU CHECK + CLEANUP ──────────
gc.collect()
torch.cuda.empty_cache()
if not torch.cuda.is_available():
    raise SystemExit("No GPU detected.")
print(f"✅ CUDA: {torch.cuda.get_device_name(0)}")

# ────────── 2. LOAD LLAMA MAVERICK MODEL (4-bit + LoRA) ──────────
model_name = "deepseek-ai/DeepSeek-V2-Lite"  # adjust if needed
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_use_double_quant=True,
    bnb_4bit_compute_dtype=torch.float16,
)

model = AutoModelForCausalLM.from_pretrained(
    model_name,
    quantization_config=bnb_config,
    device_map="auto",
    trust_remote_code=True,  # ← Add this line
)

tokenizer = AutoTokenizer.from_pretrained(
    model_name,
    use_fast=True,  # Still recommended for DeepSeek
    trust_remote_code=True,  # ← Add this line
)

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
model.gradient_checkpointing_enable()
model.config.use_cache = False
model.print_trainable_parameters()

# ────────── 3. TOKENIZER ──────────
tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=True)
if tokenizer.pad_token_id is None:
    tokenizer.pad_token_id = tokenizer.eos_token_id

# ────────── 4. LOAD INSTRUCTION DATA ──────────
records = []
with open("combined_dataset_clean.jsonl", "r") as f:
    for i, line in enumerate(f, start=1):
        try:
            rec = json.loads(line)
            instr = rec.get("instruction", "").strip()
            inp = rec.get("input", "").strip()
            out = rec.get("output", "").strip()
            if not (instr and out):
                continue
            prompt = f"{instr}\n\n{inp}" if inp else instr
            records.append({"text": f"{prompt}\n\n### Response:\n{out}"})
        except json.JSONDecodeError:
            print(f"⚠️ Skipping malformed JSON on line {i}")
print(f"✅ Loaded {len(records)} examples.")
ds = Dataset.from_list(records)


# ────────── 5. TOKENIZATION ──────────
def tokenize_fn(ex):
    tokens = tokenizer(
        ex["text"],
        truncation=True,
        padding="max_length",
        max_length=16384,  # Adjust this if your model supports higher context
    )
    tokens["labels"] = tokens["input_ids"].copy()
    return tokens


tokenized = ds.map(tokenize_fn, batched=False, remove_columns=["text"])


# ────────── 6. CUSTOM TRAINER ──────────
class SFTTrainer(Trainer):
    def compute_loss(self, model, inputs, return_outputs=False):
        labels = inputs.pop("labels")
        outputs = model(**inputs, return_dict=True)
        logits = outputs.logits
        shift_logits = logits[..., :-1, :].contiguous()
        shift_labels = labels[..., 1:].contiguous()
        loss_fct = CrossEntropyLoss(ignore_index=tokenizer.pad_token_id)
        loss = loss_fct(
            shift_logits.view(-1, shift_logits.size(-1)), shift_labels.view(-1)
        )
        return (loss, outputs) if return_outputs else loss


# ────────── 7. TRAINING CONFIG ──────────
training_args = TrainingArguments(
    output_dir="./sft_output",
    per_device_train_batch_size=1,
    gradient_accumulation_steps=4,
    gradient_checkpointing=True,
    num_train_epochs=2,
    logging_dir="./sft_output/logs",
    logging_steps=25,
    save_strategy="epoch",
    fp16=True,
    bf16=False,
)

# ────────── 8. START TRAINING ──────────
data_collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)

trainer = SFTTrainer(
    model=model,
    args=training_args,
    train_dataset=tokenized,
    data_collator=data_collator,
)

print("🚀 Training begins...")
trainer.train()

# ────────── 9. SAVE MODEL ──────────
model.save_pretrained("./sft_output")
tokenizer.save_pretrained("./sft_output")
print("✅ Model saved to ./sft_output")

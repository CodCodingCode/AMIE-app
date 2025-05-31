import os
import re
from datasets import load_dataset
from huggingface_hub import snapshot_download
from transformers import AutoTokenizer, AutoModelForCausalLM
from trl import GRPOConfig, GRPOTrainer
import torch

# ─── 0. HF TOKEN ─────────────────────────────────────────────────
HF_TOKEN = os.getenv("HUGGINGFACE_HUB_TOKEN")
print("[debug] HF_TOKEN:", HF_TOKEN[:8] + "…" if HF_TOKEN else None)
if not HF_TOKEN:
    raise RuntimeError("Missing HUGGINGFACE_HUB_TOKEN")

# ─── 1. Download model + checkpoint via snapshot_download ────────
REPO_ID = "CodCodingCode/llama-3.1-8b-clinical-v1.1"
SUBFOLDER = "checkpoint-2250"
print(f"[debug] Downloading {REPO_ID}…")
cache_dir = snapshot_download(repo_id=REPO_ID, token=HF_TOKEN)
print("[debug] snapshot_download complete, cache_dir:", cache_dir)
model_path = os.path.join(cache_dir, SUBFOLDER)
tokenizer_path = cache_dir
print("[debug] model_path exists?", os.path.isdir(model_path))
print("[debug] tokenizer_path exists?", os.path.isdir(tokenizer_path))

# ─── 2. Load tokenizer & model from disk ─────────────────────────
print("[debug] Loading tokenizer from:", tokenizer_path)
hf_tokenizer = AutoTokenizer.from_pretrained(tokenizer_path, use_fast=True)
print("[debug] hf_tokenizer type:", type(hf_tokenizer))

print("[debug] Loading model from:", model_path)
hf_model = AutoModelForCausalLM.from_pretrained(
    model_path,
    device_map="auto",
    torch_dtype=torch.bfloat16,  # ← load weights in BF16
)
hf_model.gradient_checkpointing_enable()
print("[debug] hf_model loaded. device_map:", hf_model.hf_device_map)

# ─── 3. Load & filter your dataset ────────────────────────────────
print("[debug] Loading clinical-conversations dataset…")
ds = load_dataset("CodCodingCode/clinical-conversations", split="train")
print("[debug] Original dataset size:", len(ds))
ds = ds.filter(
    lambda ex: ex["instruction"]
    != "You are simulating a real patient in conversation with their doctor."
)
print("[debug] Filtered dataset size:", len(ds))


# ─── 4. Build prompt‐only column ──────────────────────────────────
def make_prompt(ex):
    instr = ex["instruction"].strip()
    inp = ex.get("input", "").strip()
    full = instr + ("\n" + inp if inp else "")
    return {"prompt": full}


print("[debug] Mapping make_prompt…")
prompt_ds = ds.map(make_prompt, remove_columns=ds.column_names)
print("[debug] prompt_ds columns:", prompt_ds.column_names)
print("[debug] example prompt:", prompt_ds[0]["prompt"][:200].replace("\n", "\\n"))


# ─── 5. Tokenize (batched!) ───────────────────────────────────────
# ─── 5. Tokenize ──────────────────────────────────────────────────
def tokenize_batch(batch):
    print(f"[debug] Tokenizing batch of size: {len(batch['prompt'])}")
    out = hf_tokenizer(
        batch["prompt"],
        truncation=True,
        padding="max_length",
        max_length=512,
    )
    return out


print("[debug] Starting tokenization…")
# remove remove_columns, so prompt stays in the dataset
tokenized = prompt_ds.map(
    tokenize_batch,
    batched=True,
    # remove_columns=["prompt"],  ←←←  drop this line
)
print("[debug] Tokenized columns:", tokenized.column_names)
# you'll now see ['prompt','input_ids','attention_mask']
print("[debug] Tokenized dataset columns:", tokenized.column_names)
print(
    "[debug] Example tokenized features:",
    {k: tokenized[0][k] for k in tokenized.column_names},
)


# ─── 6. Define your thinking:/answer reward fn ────────────────────
def thinking_answer_reward(prompts, completions, **kwargs):
    rewards = []
    for idx, text in enumerate(completions):
        t = text.strip().lower()
        ok = (
            t.count("thinking:") == 1
            and t.count("answer:") == 1
            and t.find("thinking:") < t.find("answer:")
        )
        score = 1.0 if ok else 0.0
        print(
            f"[debug reward] #{idx} → thinking_count,answer_count,order ="
            f" {t.count('thinking:')}, {t.count('answer:')}, {t.find('thinking:') < t.find('answer:')} => {score}"
        )
        rewards.append(score)
    return rewards


# ─── 7. Configure GRPO ───────────────────────────────────────────
training_args = GRPOConfig(
    # Essential parameters
    output_dir="llama-3.1-8b-think-answer-debug",
    num_train_epochs=1,
    max_steps=2450,  # For debugging, use a small number of steps
    per_device_train_batch_size=4,  # We want to get all generations in one device batch
    bf16=True,
    # Optional but useful
    gradient_accumulation_steps=2,
    learning_rate=1e-5,
    logging_steps=10,
    # GRPO specific (optional)
)

# ─── 8. Instantiate & train ───────────────────────────────────────
trainer = GRPOTrainer(
    model=hf_model,
    args=training_args,
    train_dataset=tokenized,
    reward_funcs=thinking_answer_reward,
)
print("[debug] Starting trainer.train()…")


if __name__ == "__main__":
    trainer.train()

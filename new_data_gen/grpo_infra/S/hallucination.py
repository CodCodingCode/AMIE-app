import os
import re
from datasets import load_dataset
from huggingface_hub import snapshot_download
from transformers import AutoTokenizer, AutoModelForCausalLM
from trl import GRPOConfig, GRPOTrainer
import torch

# ─── 0. HF TOKEN ─────────────────────────────────────────────────
HF_TOKEN = "token"
print("[debug] HF_TOKEN:", HF_TOKEN[:8] + "…" if HF_TOKEN else None)
if not HF_TOKEN:
    raise RuntimeError("Missing HUGGINGFACE_HUB_TOKEN")

# ─── 1. Download model + checkpoint via snapshot_download ────────
REPO_ID = "CodCodingCode/llama-3.1-8b-clinical-v1.3"
SUBFOLDER = "checkpoint-6508"
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
ds = load_dataset("CodCodingCode/clinical-conversations-V1.2", split="train")
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

    full = f"""Instruction: {instr} 
    Input: {("\n" + inp if inp else "")} 
    Output: THINKING: 
    """
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


# ─── 6. Define your ChatGPT-based anti-hallucination reward fn ────────────────────
from openai import OpenAI
from itertools import islice
import random
import json 


# Initialize OpenAI client
client = OpenAI(api_key="api")
model = "gpt-4.1-nano"


def chatgpt_hallucination_reward(prompts, completions, **kwargs):
    rewards = []
    for idx, (prompt, completion) in enumerate(zip(prompts, completions)):

        # Extract conversation data if it's a clinical summarizer task
        if "clinical summarizer" in prompt.lower():
            # Extract conversation history
            conv_match = re.search(r"CONVERSATION HISTORY:\s*(\[.*?\])", prompt, re.DOTALL)
            # Extract previous vignette
            vignette_match = re.search(r"PREVIOUS VIGNETTE:\s*(.*?)(?:Output:|$)", prompt, re.DOTALL)
            
            if conv_match:
                conversation_history = conv_match.group(1).strip()
                previous_vignette = vignette_match.group(1).strip() if vignette_match else ""

                # Create ChatGPT prompt to evaluate hallucination
                evaluation_prompt = f"""You are an expert clinical fact-checker. Compare the conversation + previous vignette with the new clinical summary to find hallucinations.

CONVERSATION HISTORY:
{conversation_history}

PREVIOUS VIGNETTE:
{previous_vignette}

NEW CLINICAL SUMMARY TO CHECK:
{completion}

Find if the summary adds information NOT in the conversation or previous vignette.

JSON response:
- "hallucinated_items": [things added that weren't in conversation/vignette]
- "accurate_items": [things correctly from conversation/vignette]  
- "score": -10 to +10 (-10=bad hallucinations, +10=perfect)

{{"hallucinated_items": [], "accurate_items": [], "score": 0}}"""

                try:
                    response = client.chat.completions.create(
                        model=model,
                        messages=[{"role": "user", "content": evaluation_prompt}],
                        temperature=0.1,
                        max_tokens=200,
                    )

                    # Get raw response and try to extract JSON
                    raw_content = response.choices[0].message.content
                    
                    # Try to extract JSON if wrapped in markdown
                    json_match = re.search(r'\{.*\}', raw_content, re.DOTALL)
                    if json_match:
                        json_str = json_match.group(0)
                    else:
                        json_str = raw_content

                    result = json.loads(json_str)
                    score = result.get("score", 0.0)
                    hallucinated = result.get("hallucinated_items", [])
                    accurate = result.get("accurate_items", [])

                    print(
                        f"[debug reward] #{idx} → hallucinated: {hallucinated}, accurate: {accurate}, score: {score}"
                    )

                except json.JSONDecodeError as e:
                    print(f"[debug reward] #{idx} → JSON error: {e}, raw: {response.choices[0].message.content}")
                    score = 0.0
                except Exception as e:
                    print(
                        f"[debug reward] #{idx} → ChatGPT error: {e}, defaulting to 0.0"
                    )
                    score = 0.0

            else:
                score = 0.0
        else:
            score = 0.0

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
    reward_funcs=chatgpt_hallucination_reward,
)
print("[debug] Starting trainer.train()…")


if __name__ == "__main__":
    trainer.train()

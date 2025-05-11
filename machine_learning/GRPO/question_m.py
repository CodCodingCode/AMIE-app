import json
import torch
from datasets import Dataset
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    GenerationConfig,
)
from trl import PPOConfig, PPOTrainer, AutoModelForCausalLMWithValueHead

# ── 1) Load & format prompts ─────────────────────────────────────────────────────
print("🔧 Loading and formatting prompts...")
with open("medical_case.json", "r") as f:
    medical_cases = json.load(f)

instruction = (
    "You are a medical expert. You are given a doctor's vignette and your job "
    "is to generate the best possible question to ask the patient to help lead "
    "to the correct diagnosis."
)

formatted = []
for case in medical_cases:
    formatted.append(
        {
            "messages": [
                {"role": "system", "content": instruction},
                {"role": "user", "content": case["doctor_vignette"]},
            ]
        }
    )

dataset = Dataset.from_list(formatted)


# ── 2) PPO hyperparameters ───────────────────────────────────────────────────────
ppo_config = PPOConfig(
    learning_rate=1.41e-5,
    batch_size=1,
    mini_batch_size=1,
    gradient_accumulation_steps=4,
)


# ── 3) Tokenizer & policy+value on GPU ────────────────────────────────────────────
policy_tokenizer_name = "aaditya/Llama3-OpenBioLLM-8B"
print(f"🧠 Loading tokenizer from {policy_tokenizer_name}…")
tokenizer = AutoTokenizer.from_pretrained(
    policy_tokenizer_name,
    use_fast=False,
    local_files_only=True,
)
tokenizer.pad_token_id = tokenizer.eos_token_id

# **IMPORTANT**: use a relative path here so HF treats it as a folder, not a repo ID
policy_ckpt = "./llama-medical-diagnosis/checkpoint-42462"
print(f"🧠 Loading SFT+ValueHead from {policy_ckpt} onto GPU…")
policy_model: AutoModelForCausalLMWithValueHead = (
    AutoModelForCausalLMWithValueHead.from_pretrained(
        policy_ckpt,
        torch_dtype=torch.float16,
        device_map="auto",
        local_files_only=True,
    ).eval()
)

# Inject a minimal GenerationConfig so PPOTrainer can read/write eos_token_id
policy_model.generation_config = GenerationConfig(**policy_model.config.to_dict())


# ── 4) Frozen reference policy on CPU ─────────────────────────────────────────────
print("🖥️  Loading CPU‐only reference model…")
ref_model: AutoModelForCausalLMWithValueHead = (
    AutoModelForCausalLMWithValueHead.from_pretrained(
        policy_ckpt,
        torch_dtype=torch.float16,
        device_map={"": "cpu"},
        local_files_only=True,
    ).eval()
)
ref_model.generation_config = policy_model.generation_config


# ── 5) Reward network on CPU ─────────────────────────────────────────────────────
reward_name = "meta-llama/Llama-3.1-8B-Instruct"
print(f"🏅 Loading reward model {reward_name} onto CPU…")
reward_tokenizer = AutoTokenizer.from_pretrained(
    reward_name,
    use_fast=False,
    local_files_only=True,
)
reward_model = AutoModelForCausalLM.from_pretrained(
    reward_name,
    torch_dtype=torch.float16,
    device_map={"": "cpu"},
    local_files_only=True,
).eval()


def get_reward(query: str, response: str) -> float:
    with torch.no_grad():
        toks = reward_tokenizer(
            query + response,
            truncation=True,
            max_length=1024,
            return_tensors="pt",
        ).to("cpu")
        logits = reward_model(**toks).logits
        return float(logits[:, -1].mean())


# ── 6) Build PPOTrainer (positional API) ─────────────────────────────────────────
print("🚀 Initializing PPOTrainer…")
ppo_trainer = PPOTrainer(
    ppo_config,  # 1) PPOConfig
    tokenizer,  # 2) tokenizer
    policy_model,  # 3) actor+critic on GPU
    ref_model,  # 4) frozen reference on CPU
    reward_model,  # 5) reward network on CPU
    dataset,  # 6) HF dataset
    policy_model,  # 7) value_model (re‐use its value head)
)


# ── 7) PPO training loop ─────────────────────────────────────────────────────────
print("🚀 Starting PPO loop…")
for sample in dataset:
    system_msg = sample["messages"][0]["content"]
    user_msg = sample["messages"][1]["content"]
    prompt = (
        "<|system|>\n" f"{system_msg}\n" "<|user|>\n" f"{user_msg}\n" "<|assistant|>\n"
    )

    # generate on GPU
    inputs = tokenizer(prompt, return_tensors="pt").to("cuda")
    gen_ids = policy_model.generate(
        **inputs,
        max_new_tokens=64,
        pad_token_id=tokenizer.pad_token_id,
    )
    text_out = tokenizer.decode(gen_ids[0], skip_special_tokens=True)
    response = text_out.replace(prompt, "")

    # compute reward & step
    r = get_reward(prompt, response)
    print(f"[REWARD={r:.4f}] {response}")
    ppo_trainer.step([prompt], [response], [r])


# ── 8) Save fine‐tuned policy ────────────────────────────────────────────────────
print("💾 Saving final PPO‐finetuned model…")
policy_model.save_pretrained("ppo-finetuned-model")
tokenizer.save_pretrained("ppo-finetuned-model")
print("✅ Done.")

# THis is a change

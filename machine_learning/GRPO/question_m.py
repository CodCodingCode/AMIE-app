import json
import torch
from datasets import Dataset
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    GenerationConfig,
)
from trl import AutoModelForCausalLMWithValueHead, PPOConfig, PPOTrainer

# ── 0) Paths & model IDs ────────────────────────────────────────────────────────
policy_ckpt        = "/home/ubuntu/project/llama-medical-diagnosis/checkpoint-42462"
base_tokenizer_id  = "aaditya/Llama3-OpenBioLLM-8B"
reward_model_id    = "meta-llama/Llama-3.1-8B-Instruct"
device             = "cuda"  # or "cpu"

# ── 1) Load & format your prompts ───────────────────────────────────────────────
print("🔧 Loading and formatting prompts…")
with open("medical_case.json", "r") as f:
    cases = json.load(f)

instruction = (
    "You are a medical expert. You are given a doctor's vignette and your job "
    "is to generate the best possible question to ask the patient to help lead "
    "to the correct diagnosis."
)
formatted = [
    {
        "messages": [
            {"role": "system", "content": instruction},
            {"role": "user",   "content": c["doctor_vignette"]},
        ]
    }
    for c in cases
]
dataset = Dataset.from_list(formatted)

# ── 2) PPO hyperparameters ─────────────────────────────────────────────────────
ppo_config = PPOConfig(
    learning_rate=1.41e-5,
    batch_size=1,
    mini_batch_size=1,
    gradient_accumulation_steps=4,
)

# ── 3) Tokenizer & policy+value on GPU ─────────────────────────────────────────
print(f"🧠 Loading tokenizer from {base_tokenizer_id}…")
tokenizer = AutoTokenizer.from_pretrained(
    base_tokenizer_id,
    use_fast=False,
    local_files_only=True,
)
# ensure a pad token
if tokenizer.pad_token_id is None:
    tokenizer.pad_token_id = tokenizer.eos_token_id

print(f"🧠 Loading your SFT+LoRA checkpoint (policy) from {policy_ckpt}…")
policy_model: AutoModelForCausalLMWithValueHead = (
    AutoModelForCausalLMWithValueHead
    .from_pretrained(
        policy_ckpt,
        torch_dtype=torch.float16,
        device_map="auto",
        local_files_only=True,
    )
    .eval()
)
# give it the bare‐minimum GenerationConfig so PPOTrainer can set eos_token_id
policy_model.generation_config = GenerationConfig(**policy_model.config.to_dict())

# ── 4) Frozen reference policy on CPU ───────────────────────────────────────────
print("🖥️  Loading CPU‐only reference policy…")
ref_model: AutoModelForCausalLMWithValueHead = (
    AutoModelForCausalLMWithValueHead
    .from_pretrained(
        policy_ckpt,
        torch_dtype=torch.float16,
        device_map={"": "cpu"},
        local_files_only=True,
    )
    .eval()
)
ref_model.generation_config = policy_model.generation_config

# ── 5) Reward network on CPU ────────────────────────────────────────────────────
print(f"🏅 Loading reward LM {reward_model_id} onto CPU…")
reward_tokenizer = AutoTokenizer.from_pretrained(
    reward_model_id,
    use_fast=False,
    local_files_only=True,
)
reward_model = (
    AutoModelForCausalLM
    .from_pretrained(
        reward_model_id,
        torch_dtype=torch.float16,
        device_map={"": "cpu"},
        local_files_only=True,
    )
    .eval()
)

def get_reward(query: str, response: str) -> float:
    # use next‐token logit average as a simple scalar reward
    with torch.no_grad():
        toks = reward_tokenizer(
            query + response,
            truncation=True,
            max_length=1024,
            return_tensors="pt",
        ).to("cpu")
        logits = reward_model(**toks).logits
        return float(logits[:, -1].mean())

# ── 6) Initialize PPOTrainer (positional API) ──────────────────────────────────
print("🚀 Initializing PPOTrainer…")
ppo_trainer = PPOTrainer(
    ppo_config,     # 1) PPOConfig
    tokenizer,      # 2) tokenizer
    policy_model,   # 3) actor+critic
    ref_model,      # 4) frozen reference
    reward_model,   # 5) reward network
    dataset,        # 6) HF dataset
    policy_model,   # 7) value_model (re‐use attached value head)
)

# ── 7) PPO loop ───────────────────────────────────────────────────────────────
print("🚀 Starting PPO loop…")
for sample in dataset:
    sys_msg = sample["messages"][0]["content"]
    usr_msg = sample["messages"][1]["content"]
    prompt  = (
        "<|system|>\n" + sys_msg +
        "\n<|user|>\n" + usr_msg +
        "\n<|assistant|>\n"
    )

    # generate
    inputs  = tokenizer(prompt, return_tensors="pt").to(device)
    gen_ids = policy_model.generate(
        **inputs,
        max_new_tokens=64,
        pad_token_id=tokenizer.pad_token_id,
    )
    text_out = tokenizer.decode(gen_ids[0], skip_special_tokens=True)
    response = text_out.replace(prompt, "")

    # score & update
    r = get_reward(prompt, response)
    print(f"[REWARD={r:.4f}] {response}")
    ppo_trainer.step([prompt], [response], [r])

# ── 8) Save your fine‐tuned policy ───────────────────────────────────────────────
print("💾 Saving final PPO‐finetuned model…")
policy_model.save_pretrained("ppo-finetuned-model")
tokenizer.save_pretrained("ppo-finetuned-model")
print("✅ Done.")
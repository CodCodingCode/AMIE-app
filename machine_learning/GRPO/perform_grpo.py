from trl import PPOConfig, PPOTrainer, AutoModelForCausalLMWithValueHead
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    GenerationConfig,
)
from datasets import load_dataset
import torch

# 1) Load your prompts
raw = load_dataset("json", data_files="medical_case.json")["train"]
dataset = raw.map(lambda x: {"query": x["doctor_vignette"]})

# 2) Shared tokenizer (just download from HF)
policy_repo = "aaditya/Llama3-OpenBioLLM-8B"
tokenizer   = AutoTokenizer.from_pretrained(policy_repo, use_fast=False)
tokenizer.pad_token_id = tokenizer.eos_token_id

# 3) Policy+Value (PEFT) on GPU
ckpt = "/home/ubuntu/project/llama-medical-diagnosis/checkpoint-42462"
policy_model = AutoModelForCausalLMWithValueHead.from_pretrained(
    ckpt,
    torch_dtype=torch.float16,
    device_map="auto",            # <<< shard across GPUs if you have >1 H100
    offload_folder="offload",      # optional: spills CPU if needed
    offload_state_dict=True,      # optional
).eval()
# so .generate() works
policy_model.generation_config = GenerationConfig(**policy_model.config.to_dict())

# 4) Frozen reference policy on GPU
ref_model = AutoModelForCausalLM.from_pretrained(
    policy_repo,
    torch_dtype=torch.float16,
    device_map="auto",
).eval()
ref_model.generation_config = policy_model.generation_config

# 5) Reward LLM on GPU
reward_repo  = "meta-llama/Llama-3.1-8B-Instruct"
reward_tokenizer = AutoTokenizer.from_pretrained(reward_repo)
reward_model     = AutoModelForCausalLM.from_pretrained(
    reward_repo,
    torch_dtype=torch.float16,
    device_map="auto",
).eval()

def get_reward(query: str, response: str) -> float:
    toks = reward_tokenizer(
        query + response,
        truncation=True,
        max_length=1024,
        return_tensors="pt",
    ).to(policy_model.device)  # already GPU
    with torch.no_grad():
        logits = reward_model(**toks).logits
        # use average next‐token logit
        return float(logits[:, -1].mean())

# 6) PPO hyperparams
ppo_config = PPOConfig(
    learning_rate=1.41e-5,
    batch_size=4,
    mini_batch_size=1,
    gradient_accumulation_steps=1,
)

# 7) Build PPOTrainer (positional API)
ppo_trainer = PPOTrainer(
    ppo_config,          # your PPOConfig
    tokenizer,           # HuggingFace tokenizer
    policy_model,        # actor+critic (PEFT w/ value head)
    ref_model,           # frozen reference
    reward_model,        # reward network
    train_dataset=dataset,# HF dataset
    value_model=policy_model,# reuse the attached value head
)

# 8) PPO loop
for sample in dataset:
    q = sample["query"]
    inputs = tokenizer(q, return_tensors="pt").to(policy_model.device)
    gen_ids = policy_model.generate(
        **inputs,
        max_new_tokens=128,
        pad_token_id=tokenizer.pad_token_id,
    )
    resp = tokenizer.decode(
        gen_ids[0, inputs.input_ids.shape[-1]:],
        skip_special_tokens=True,
    )

    r = get_reward(q, resp)
    print(f"[REWARD={r:.4f}] {resp}")

    ppo_trainer.step([q], [resp], [r])

# 9) Save
policy_model.save_pretrained("ppo-finetuned")
tokenizer.save_pretrained("ppo-finetuned")
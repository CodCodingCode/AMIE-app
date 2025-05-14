import os
import gc
import torch
from transformers import (
    AutoTokenizer,
    BitsAndBytesConfig,
    GenerationConfig,
)
from peft import PeftModel
from trl import (
    AutoModelForCausalLMWithValueHead,
    PPOConfig,
    PPOTrainer,
)

# 1. Cleanup & GPU check
gc.collect()
torch.cuda.empty_cache()
if not torch.cuda.is_available():
    raise SystemExit("No GPU detected. Exiting.")

# 2. Directories & model IDs
SFT_DIR = "./ppo_ready_output"       # your LoRA+value-head folder
BASE = "aaditya/Llama3-OpenBioLLM-8B"  # base model name

# 3. Tokenizer
tokenizer = AutoTokenizer.from_pretrained(SFT_DIR, use_fast=False)
if tokenizer.pad_token_id is None:
    tokenizer.pad_token_id = tokenizer.eos_token_id

# 4. Load policy with value head & LoRA adapters
bnb = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_use_double_quant=True,
    bnb_4bit_compute_dtype=torch.float16,
)



policy = PeftModel.from_pretrained(
    PeftModel.from_pretrained(
        AutoModelForCausalLMWithValueHead.from_pretrained(
            BASE,
            quantization_config=bnb,
            device_map="auto",
            torch_dtype=torch.float16,
        ),
        SFT_DIR,
        device_map="auto",
        torch_dtype=torch.float16,
    )
)
policy.eval()
# ensure .generate() works
policy.base_model.generation_config = GenerationConfig(**policy.base_model.config.to_dict())

# 5. Reference model (frozen)
ref_model = AutoModelForCausalLMWithValueHead.from_pretrained(
    BASE,
    torch_dtype=torch.float16,
    device_map="cpu",
)
ref_model.eval()
ref_model.generation_config = policy.base_model.generation_config

delve_reward = AutoModelForCausalLMWithValueHead.from_pretrained(
    BASE,
    torch_dtype=torch.float16,
    device_map="cpu",
).eval()

# 6. Reward function (example: use value head last token)
def get_reward(prompt: str, response: str) -> float:
    # concatenate prompt+response for value head scoring
    batch = tokenizer(prompt + response, return_tensors="pt", truncation=True, max_length=1024)
    with torch.no_grad():
        outputs = delve_reward(**batch)
        # we take last token state-value as reward proxy
        return outputs.value.detach().cpu().item()

# 7. PPO setup
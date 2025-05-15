# save.py
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
import torch

BASE = "deepseek-ai/DeepSeek-V2-Lite"  # remote base you fine-tuned against
ADAPTER = "sft_output"  # your local LoRA+value-head folder
OUT = "full_model"  # where to dump the merged model
REPO = "CodCodingCode/DeepSeek-V2-med"  # Hub repo (create in advance)

# 1) load remote base
base = AutoModelForCausalLM.from_pretrained(
    BASE,
    torch_dtype=torch.float16,
    device_map="auto",
    trust_remote_code=True,
)

# 2) reload your local tokenizer (100 002 tokens)
tokenizer = AutoTokenizer.from_pretrained(
    ADAPTER,
    use_fast=False,
    trust_remote_code=True,
)
tokenizer.pad_token_id = tokenizer.pad_token_id or tokenizer.eos_token_id

# 3) resize the base’s embeddings to match your tokenizer
base.resize_token_embeddings(len(tokenizer))

# 4) load your LoRA adapter on top of that resized base
model = PeftModel.from_pretrained(
    base,
    ADAPTER,
    torch_dtype=torch.float16,
    device_map="auto",
    trust_remote_code=True,
)

# 5) merge LoRA weights back into the base
merged = model.merge_and_unload()

# 6) save locally
merged.save_pretrained(OUT)
tokenizer.save_pretrained(OUT)

# 7) push to Hugging Face
merged.push_to_hub(REPO, use_auth_token=True)
tokenizer.push_to_hub(REPO, use_auth_token=True)

print(f"✅ merged model + tokenizer pushed to https://huggingface.co/{REPO}")

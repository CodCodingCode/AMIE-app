from huggingface_hub import hf_hub_download
import os

# ——— CONFIG ———
REPO_ID = "CodCodingCode/llama-3.1-8b-clinical"
SUBDIR = "checkpoint-45000"
HF_TOKEN = os.getenv("HUGGINGFACE_HUB_TOKEN")  # make sure you set this in Secrets

# Ensure output directory exists
os.makedirs(SUBDIR, exist_ok=True)

# List of shards to download
shards = [
    "model-00001-of-00004.safetensors",
    "model-00002-of-00004.safetensors",
    "model-00003-of-00004.safetensors",
    "model-00004-of-00004.safetensors",
    "model.safetensors.index.json",  # the index file
]

for fname in shards:
    local_path = hf_hub_download(
        repo_id=REPO_ID,
        filename=f"{SUBDIR}/{fname}",
        token=HF_TOKEN,
        local_dir=".",  # download into the Space root
        local_dir_use_symlinks=False,  # ensure actual file copy
    )
    print(f"Downloaded {fname} to {local_path}")

from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import os

# Check what checkpoints you have
checkpoint_dir = "llama-3.1-8b-think-answer-debug"
checkpoints = [d for d in os.listdir(checkpoint_dir) if d.startswith("checkpoint-")]
checkpoints.sort(key=lambda x: int(x.split("-")[1]))  # Sort by step number

print("Available checkpoints:")
for cp in checkpoints:
    print(f"  - {cp}")

# Get the latest checkpoint
latest_checkpoint = checkpoints[-1] if checkpoints else None
print(f"\nLatest checkpoint: {latest_checkpoint}")

# Use your existing paths and token
HF_TOKEN = os.getenv("HUGGINGFACE_HUB_TOKEN", "api")

# Load from your latest checkpoint
checkpoint_path = os.path.join("llama-3.1-8b-think-answer-debug", latest_checkpoint)

print(f"[debug] Loading model from checkpoint: {checkpoint_path}")
model = AutoModelForCausalLM.from_pretrained(
    checkpoint_path,
    device_map="auto",
    torch_dtype=torch.bfloat16,
)

# Load tokenizer from the original base model instead
print("[debug] Loading tokenizer from original base model...")
try:
    tokenizer = AutoTokenizer.from_pretrained(
        "CodCodingCode/llama-3.1-8b-clinical-v1.2", token=HF_TOKEN
    )
    print("[success] Tokenizer loaded from base model")
except Exception as e:
    print(f"[error] Failed to load from base model: {e}")
    # Fallback to meta-llama tokenizer
    print("[debug] Trying meta-llama/Llama-3.1-8B as fallback...")
    tokenizer = AutoTokenizer.from_pretrained("meta-llama/Llama-3.1-8B", token=HF_TOKEN)
    print("[success] Tokenizer loaded from meta-llama")

# Save as final model
final_model_path = "llama-3.1-8b-clinical-thinking-final"
print(f"[debug] Saving final model to: {final_model_path}")

model.save_pretrained(final_model_path)
tokenizer.save_pretrained(final_model_path)

print(f"[success] Model saved to {final_model_path}")

# Now push to Hub
from huggingface_hub import HfApi

HUB_MODEL_NAME = "CodCodingCode/llama-3.1-8b-grpo-v1.2"  # ← CHANGE THIS!

api = HfApi()

# Create repository
try:
    api.create_repo(
        repo_id=HUB_MODEL_NAME,
        token=HF_TOKEN,
        private=False,  # Set to True for private repo
        exist_ok=True,
    )
    print(f"[debug] Repository created/verified: {HUB_MODEL_NAME}")
except Exception as e:
    print(f"[error] Repository creation: {e}")

# Upload the model
try:
    api.upload_folder(
        folder_path=final_model_path,
        repo_id=HUB_MODEL_NAME,
        token=HF_TOKEN,
        commit_message=f"GRPO-trained model from {latest_checkpoint}",
    )
    print(f"[success] Model uploaded to: https://huggingface.co/{HUB_MODEL_NAME}")
except Exception as e:
    print(f"[error] Upload failed: {e}")

print(f"🎉 Complete! Model available at: https://huggingface.co/{HUB_MODEL_NAME}")

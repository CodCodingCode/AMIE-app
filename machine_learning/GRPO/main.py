# train_biollama_grpo.py

from datasets import load_dataset
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import PeftModel
from trl import GRPOTrainer, GRPOConfig
import torch


# === Load Local JSONL Dataset ===
dataset = load_dataset(
    "json",
    data_files="your_data.jsonl",  # ADD DATASET PATH
    split="train",
    keep_in_memory=True,
)


# === Define Custom Reward Function ===
def reward_func(completions, ground_truth=None, **kwargs):
    """Reward 1 if completion matches ground truth exactly, else 0."""
    return [
        1.0 if c.strip() == gt.strip() else 0.0
        for c, gt in zip(completions, ground_truth)
    ]


# === Load SFT Fine-Tuned BioLLaMA Model (Half-Precision) ===
# Note: No BitsAndBytesConfig needed if loading a non-quantized, fine-tuned model

# Determine the appropriate dtype (bfloat16 if supported, otherwise float16)
compute_dtype = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
print(f"Using compute dtype: {compute_dtype}")

# Load the fine-tuned model directly in half-precision
model = AutoModelForCausalLM.from_pretrained(
    "path_to_your_SFT_biollama",  # <<< CHANGE THIS: Path to your SFT model directory or Hub ID
    torch_dtype=compute_dtype,  # Load in bf16 or fp16
    device_map="auto",  # Automatically distribute across available GPUs
    trust_remote_code=True,  # If required by the model
)
print(f"Loaded SFT model from path_to_your_SFT_biollama in {compute_dtype}")

# Load tokenizer associated with the SFT model
tokenizer = AutoTokenizer.from_pretrained(
    "path_to_your_SFT_biollama",  # <<< CHANGE THIS: Path to your SFT model directory or Hub ID
    use_fast=True,
    trust_remote_code=True,  # If required by the tokenizer
)
tokenizer.pad_token = tokenizer.eos_token  # Required for left padding

# Note: No need to load a separate PEFT adapter if the SFT model already includes it
# or if it was fully fine-tuned. If the SFT *was* a PEFT adapter, you'd load the base
# model first (potentially quantized or not) and then apply the adapter.


# === Configure GRPO ===
grpo_config = GRPOConfig(
    output_dir="./biollama-grpo-output",
    per_device_train_batch_size=1,
    bf16=True,
    gradient_checkpointing=True,
    num_train_epochs=1,
    logging_steps=10,
    max_prompt_length=512,
    max_completion_length=256,
    loss_type="dr_grpo",  # Recommended to reduce length bias
    beta=0.04,
    use_vllm=False,  # Set to True only if you're using vLLM
)

# === Initialize GRPOTrainer ===
trainer = GRPOTrainer(
    model=model,
    args=grpo_config,
    reward_funcs=reward_func,
    train_dataset=dataset,
    processing_class=tokenizer,
)

# === Start Training ===
trainer.train()

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




similarity_model = MODEL #Use a model like Llama Maverick

def reward_func_questions(completions, ground_truth=None, **kwargs):
    """Reward based on semantic similarity to the ground truth question."""
    if ground_truth is None:
        # Handle cases where ground_truth might not be provided (shouldn't happen with your dataset)
        return [0.0] * len(completions)

    # Ensure inputs are lists of strings
    completions_str = [str(c).strip() for c in completions]
    ground_truth_str = [str(gt).strip() for gt in ground_truth] # Assuming ground_truth is passed correctly

    # Compute embeddings
    # Handle potential empty strings
    completions_str = [s if s else "[PAD]" for s in completions_str]
    ground_truth_str = [s if s else "[PAD]" for s in ground_truth_str]

    try:
        comp_embeddings = similarity_model.encode(completions_str, convert_to_tensor=True)
        gt_embeddings = similarity_model.encode(ground_truth_str, convert_to_tensor=True)

        # Compute cosine similarity
        cosine_scores = util.cos_sim(comp_embeddings, gt_embeddings)

        # Extract the diagonal scores (similarity of each completion with its corresponding ground truth)
        # Clamp scores between 0 and 1 (optional, but good practice for rewards)
        rewards = [max(0.0, min(1.0, cosine_scores[i, i].item())) for i in range(len(completions))]
    except Exception as e:
        print(f"Error during reward calculation: {e}")
        print(f"Completions: {completions_str}")
        print(f"Ground Truth: {ground_truth_str}")
        rewards = [0.0] * len(completions) # Return zero reward on error

    return rewards

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

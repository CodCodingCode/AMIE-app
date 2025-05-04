import os
import json
import torch
from datasets import Dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
)
from peft import (
    get_peft_model,
    LoraConfig,
    TaskType,
    prepare_model_for_kbit_training,
)
from trl import SFTTrainer, SFTConfig  # Added SFTConfig import

# Configuration
MODEL_NAME = "meta-llama/Llama-2-7b-chat-hf"  # Choose an appropriate model
DATASET_PATH = (
    "/Users/owner/Downloads/coding projects/AMIE-app/datasets/full_dataset.json"
)
OUTPUT_DIR = "/Users/owner/Downloads/coding projects/AMIE-app/fine_tuned_model"
USE_LORA = True  # Set to False for full fine-tuning (requires more GPU memory)


def load_dataset(dataset_path):
    """Load the combined dataset and convert to the HF Dataset format."""
    with open(dataset_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Convert to the format expected by HF Dataset
    dataset_dict = {"instruction": [], "input": [], "output": []}

    for entry in data:
        dataset_dict["instruction"].append(entry["instruction"])
        dataset_dict["input"].append(entry["input"])
        dataset_dict["output"].append(entry["output"])

    return Dataset.from_dict(dataset_dict)


def format_prompt(instruction, input_text):
    """Format the prompt for the model."""
    if input_text:
        return f"<s>[INST] {instruction} \n\n {input_text} [/INST]"
    else:
        return f"<s>[INST] {instruction} [/INST]"


def tokenize_function(examples, tokenizer):
    """Tokenize and format examples for training."""
    prompts = [
        format_prompt(instruction, input_text)
        for instruction, input_text in zip(examples["instruction"], examples["input"])
    ]

    # Tokenize prompts and responses
    tokenized_prompts = tokenizer(prompts, truncation=True, padding=False)
    tokenized_outputs = tokenizer(examples["output"], truncation=True, padding=False)

    # Create input_ids by combining prompt and response tokens
    input_ids = []
    attention_mask = []

    for p_ids, p_mask, o_ids in zip(
        tokenized_prompts["input_ids"],
        tokenized_prompts["attention_mask"],
        tokenized_outputs["input_ids"],
    ):
        # Combine prompt and response (excluding BOS token from response)
        combined_ids = p_ids + o_ids[1:] + [tokenizer.eos_token_id]
        combined_mask = p_mask + [1] * (len(o_ids) - 1) + [1]  # -1 for BOS token

        input_ids.append(combined_ids)
        attention_mask.append(combined_mask)

    result = {"input_ids": input_ids, "attention_mask": attention_mask}

    # For training with SFTTrainer, we need labels
    result["labels"] = result["input_ids"].copy()

    return result


def main():
    # Load the dataset
    print("Loading dataset...")
    dataset = load_dataset(DATASET_PATH)
    print(f"Loaded dataset with {len(dataset)} examples")

    # Split into train and validation sets
    dataset = dataset.train_test_split(test_size=0.1)

    # Load the model and tokenizer
    print(f"Loading model and tokenizer: {MODEL_NAME}")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

    # Add padding token if not present
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # Handle different model loading scenarios
    if USE_LORA:
        print("Using LoRA for parameter-efficient fine-tuning")
        model = AutoModelForCausalLM.from_pretrained(
            MODEL_NAME,
            torch_dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32,
            load_in_8bit=True if torch.cuda.is_available() else False,
        )

        # Prepare model for training
        if torch.cuda.is_available():
            model = prepare_model_for_kbit_training(model)

        # Configure LoRA
        lora_config = LoraConfig(
            r=16,  # Rank
            lora_alpha=32,
            target_modules=["q_proj", "k_proj", "v_proj"],
            lora_dropout=0.05,
            bias="none",
            task_type=TaskType.CAUSAL_LM,
        )

        model = get_peft_model(model, lora_config)
        model.print_trainable_parameters()
    else:
        print("Using full fine-tuning")
        model = AutoModelForCausalLM.from_pretrained(
            MODEL_NAME,
            torch_dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32,
        )

    # Replace TrainingArguments with SFTConfig
    training_args = SFTConfig(
        output_dir=OUTPUT_DIR,
        num_train_epochs=3,
        per_device_train_batch_size=4,
        gradient_accumulation_steps=4,
        save_steps=500,
        logging_steps=100,
        learning_rate=2e-5,
        weight_decay=0.01,
        fp16=torch.cuda.is_available(),
        bf16=False,  # Can be True if your GPU supports it
        max_grad_norm=0.3,
        warmup_ratio=0.03,
        group_by_length=True,
        report_to="none",  # Change to "wandb" if using Weights & Biases
        # Move these parameters from SFTTrainer to SFTConfig
        max_seq_length=512,
        packing=False,
    )

    # Create the SFT trainer with simplified parameters
    trainer = SFTTrainer(
        model=model,
        args=training_args,
        train_dataset=dataset["train"],
        eval_dataset=dataset["test"],
        processing_class=tokenizer,  # Changed from tokenizer to processing_class
        formatting_func=lambda example: format_prompt(
            example["instruction"], example["input"]
        )
        + " "
        + example["output"],
    )

    # Train the model
    print("Starting training...")
    trainer.train()

    # Save the final model
    model.save_pretrained(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)
    print(f"Model and tokenizer saved to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()

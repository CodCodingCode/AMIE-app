import os
import gc
import time
import torch
from datasets import load_dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling,
    BitsAndBytesConfig,
)

# ADD PEFT IMPORTS
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training

# Force clean memory at start
gc.collect()
if torch.cuda.is_available():
    print("CUDA is available. Clearing cache.")
    torch.cuda.empty_cache()
else:
    print("CUDA not available. Cannot run large model without GPU.")
    exit()

# 🧠 Load model with 4-bit Quantization
model_name = "aaditya/Llama3-OpenBioLLM-8B"
print(f"Loading model: {model_name} with 4-bit quantization")

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_use_double_quant=True,
)

model = AutoModelForCausalLM.from_pretrained(
    model_name,
    quantization_config=bnb_config,
    device_map="auto",
    low_cpu_mem_usage=True,
    trust_remote_code=True,
)

# --- PEFT Setup ---
# 1. Prepare model for k-bit training (gradient checkpointing, etc.)
model = prepare_model_for_kbit_training(model)

# 2. Define LoRA configuration
lora_config = LoraConfig(
    r=16,  # Rank of the update matrices. Lower rank = fewer parameters to train.
    lora_alpha=32,  # Alpha parameter for scaling. alpha/r controls the magnitude.
    target_modules=[
        "q_proj",
        "k_proj",
        "v_proj",
        "o_proj",
    ],  # Target specific modules for LoRA adapters (common for Llama)
    lora_dropout=0.05,  # Dropout probability for LoRA layers
    bias="none",  # Usually set to 'none' for LoRA
    task_type="CAUSAL_LM",  # Specify the task type
)

# 3. Get the PEFT model
model = get_peft_model(model, lora_config)
print("PEFT model created:")
model.print_trainable_parameters()  # Shows how many parameters are actually trainable (should be small %)
# --- End PEFT Setup ---

tokenizer = AutoTokenizer.from_pretrained(model_name)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

# 📂 Load dataset
dataset_path = "datasets/combined_sft_dataset.json"
dataset = load_dataset("json", data_files=dataset_path, split="train")
print(f"Using {len(dataset)} examples for training")


def format_example(example):
    """Format the example for training"""
    text = f"Diagnosis: {example['output'].strip()}\n"
    return {"text": text}


dataset = dataset.map(format_example)


# Prepare dataset for training
def tokenize_function(examples):
    return tokenizer(examples["text"], truncation=True, max_length=64)


tokenized_dataset = dataset.map(
    tokenize_function, batched=True, remove_columns=["output"]
)

# TrainingArguments for PEFT/quantized models
training_args = TrainingArguments(
    output_dir="./gpu_model_output_4bit_peft",  # New output dir
    per_device_train_batch_size=1,  # Can potentially increase slightly with PEFT
    gradient_accumulation_steps=4,
    num_train_epochs=1,  # Might need more epochs for PEFT to converge
    save_strategy="epoch",
    logging_steps=10,
    learning_rate=2e-4,  # PEFT often uses a higher learning rate than full fine-tuning
    weight_decay=0.01,
    fp16=False,  # Keep False for bitsandbytes
    bf16=torch.cuda.is_bf16_supported(),
)

# Use a simple data collator
data_collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)

# Create trainer - PASS THE PEFT MODEL
trainer = Trainer(
    model=model,  # Use the PEFT model here
    args=training_args,
    train_dataset=tokenized_dataset,
    data_collator=data_collator,
)


# Memory safeguard (still useful)
def memory_cleanup():
    """Clean memory periodically"""
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


print("Starting PEFT training on quantized model...")

# Override training step (optional, but can help with memory on long runs)
original_training_step = trainer.training_step


def training_step_with_cleanup(*args, **kwargs):
    if (
        trainer.state.global_step > 0 and trainer.state.global_step % 50 == 0
    ):  # Cleanup every 50 steps
        memory_cleanup()
    return original_training_step(*args, **kwargs)


trainer.training_step = training_step_with_cleanup

# Start training
try:
    train_result = trainer.train()
    print("Training completed at:", time.strftime("%H:%M:%S"))
    print(train_result)

    # Save the PEFT adapter model (not the whole base model)
    print("Saving PEFT adapter model to ./gpu_model_output_4bit_peft...")
    # Use save_pretrained for PEFT models - saves only the adapter config/weights
    model.save_pretrained("./gpu_model_output_4bit_peft")
    # Optionally save the tokenizer too
    tokenizer.save_pretrained("./gpu_model_output_4bit_peft")
    print("PEFT Adapter model saved successfully!")

    # --- Testing PEFT Model ---
    # For testing, you typically load the base quantized model again
    # and then load the adapter weights on top.
    # However, the 'model' object in memory *is* the merged model after training.
    # So we can use it directly here for simplicity.
    # If loading later, you'd do:
    # base_model = AutoModelForCausalLM.from_pretrained(model_name, quantization_config=bnb_config, device_map="auto")
    # peft_model = PeftModel.from_pretrained(base_model, "./gpu_model_output_4bit_peft")
    # merged_model = peft_model.merge_and_unload() # Optional: merge for faster inference if memory allows

    print("\nTesting the trained PEFT model with a sample prompt:")
    test_text = "What is the diagnosis for a patient with severe fatigue, joint pain, and butterfly rash on the face?"
    # Ensure model is in eval mode for generation
    model.eval()
    device = model.device  # PEFT model should report its device correctly
    inputs = tokenizer(test_text, return_tensors="pt").to(device)

    with torch.no_grad():  # Disable gradients for inference
        outputs = model.generate(
            **inputs,
            max_new_tokens=50,
            num_return_sequences=1,
            temperature=0.7,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id,
        )

    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    if response.startswith(test_text):
        response = response[len(test_text) :].strip()

    print(f"\nPrompt: {test_text}")
    print(f"Response: {response}")
    print("\nPEFT Model trained and tested.")

except Exception as e:
    print(f"Training error: {str(e)}")
    import traceback

    traceback.print_exc()
    print("\nPotential issues:")
    print(
        "1. GPU Out of Memory: Try reducing batch size, gradient accumulation steps, or max_length."
    )
    print(
        "2. Model Size: Llama3-8B is large. Ensure your GPU has sufficient VRAM (e.g., >16GB, ideally 24GB+)."
    )
    print("3. Library versions: Ensure torch, transformers, datasets are compatible.")
    print(
        "4. PEFT Issues: Ensure target_modules in LoraConfig are correct for the model architecture."
    )
 
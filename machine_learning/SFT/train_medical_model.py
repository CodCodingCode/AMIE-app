# ✅ H100-optimized PEFT training without bitsandbytes (FP16-based)

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
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training

# Memory cleanup
gc.collect()
if torch.cuda.is_available():
    print(f"CUDA is available. GPU: {torch.cuda.get_device_name(0)}")
    torch.cuda.empty_cache()
else:
    print("CUDA not available. Cannot continue without GPU.")
    exit()

# Model config
model_name = "aaditya/Llama3-OpenBioLLM-8B"
print(f"Loading model: {model_name} using FP16")

model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype=torch.float16,
    device_map="auto",
    trust_remote_code=True,
)

model = prepare_model_for_kbit_training(model)


lora_config = LoraConfig(
    r=16,
    lora_alpha=32,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM",
)
lora_config.use_rslora = False  # <== ✅ prevent BNB fallback
model = get_peft_model(model, lora_config)
model.print_trainable_parameters()

tokenizer = AutoTokenizer.from_pretrained(model_name)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

dataset_path = "combined_dataset.jsonl"
dataset = load_dataset("json", data_files=dataset_path, split="train")
print(f"Loaded {len(dataset)} training examples.")


def format_example(example):
    return {"text": f"Diagnosis: {example['output'].strip()}\n"}


dataset = dataset.map(format_example)


def tokenize_function(examples):
    return tokenizer(examples["text"], truncation=True, max_length=64)


tokenized_dataset = dataset.map(
    tokenize_function, batched=True, remove_columns=["output"]
)

training_args = TrainingArguments(
    output_dir="./h100_fp16_peft_output",
    per_device_train_batch_size=2,
    gradient_accumulation_steps=2,
    num_train_epochs=1,
    save_strategy="epoch",
    logging_steps=10,
    learning_rate=2e-4,
    weight_decay=0.01,
    fp16=True,  # Use native mixed precision
    bf16=False,  # disable bf16 here unless you explicitly want it
)

data_collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_dataset,
    data_collator=data_collator,
)


def memory_cleanup():
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


def training_step_with_cleanup(*args, **kwargs):
    if trainer.state.global_step > 0 and trainer.state.global_step % 50 == 0:
        memory_cleanup()
    return original_training_step(*args, **kwargs)


print("Starting training...")
original_training_step = trainer.training_step
trainer.training_step = training_step_with_cleanup

try:
    train_result = trainer.train()
    print("Training complete.", train_result)

    model.save_pretrained("./h100_fp16_peft_output")
    tokenizer.save_pretrained("./h100_fp16_peft_output")

    print("\nTesting trained model:")
    test_text = "What is the diagnosis for a patient with severe fatigue, joint pain, and butterfly rash on the face?"
    model.eval()
    inputs = tokenizer(test_text, return_tensors="pt").to(model.device)

    with torch.no_grad():
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

    print(f"\nPrompt: {test_text}\nResponse: {response}")

except Exception as e:
    import traceback

    print("Training error:", str(e))
    traceback.print_exc()

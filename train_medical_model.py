from datasets import load_dataset
from transformers import AutoModelForCausalLM, AutoTokenizer
from trl import SFTTrainer, SFTConfig

# 🧠 Load model and tokenizer
model_name = "aaditya/Llama3-OpenBioLLM-8B"
model = AutoModelForCausalLM.from_pretrained(model_name)
tokenizer = AutoTokenizer.from_pretrained(model_name)
tokenizer.pad_token = (
    tokenizer.eos_token
)  # optional, but recommended for training stability

# 📂 Load dataset (local JSONL file)
dataset_path = "datasets/medical_blind_diagnostic_format.jsonl"
dataset = load_dataset("json", data_files=dataset_path, split="train")

# ✅ (Optional) Combine prompt + completion into one field if not already done
# Example only if your dataset has 'prompt' and 'completion' fields:
# dataset = dataset.map(lambda x: {"text": f"{x['prompt']}\n{x['completion']}"})


def format_example(example):
    return {
        "text": (
            f"### Instruction:\n{example['instruction']}\n\n"
            f"### Case:\n{example['input'].strip()}\n\n"
            f"### Patient Statement:\n{example['patient_statement'].strip()}\n\n"
            f"### Question:\n{example['expected_question'].strip()}"
        )
    }


dataset = dataset.map(format_example)

# ⚙️ Define SFT configuration (tell it to use 'text' field)
training_args = SFTConfig(
    output_dir="./sft_output",
    per_device_train_batch_size=4,
    num_train_epochs=3,
    logging_steps=50,
    save_steps=200,
    learning_rate=2e-5,
    max_length=512,
    packing=True,
    dataset_text_field="text",  # ✅ point to the text field
)

# 🚀 Create trainer
trainer = SFTTrainer(
    model=model,
    train_dataset=dataset,
    args=training_args,
    processing_class=tokenizer,  # ✅ replaces 'tokenizer='
)

# 🎯 Start training
trainer.train()

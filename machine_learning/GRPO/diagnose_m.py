import json
import torch
from datasets import Dataset
from transformers import AutoTokenizer, AutoModelForCausalLM
from trl import PPOTrainer, PPOConfig, AutoModelForCausalLMWithValueHead

# Step 1: Prepare prompt dataset from medical_case.json
print("🔧 Loading and formatting prompts...")
with open("medical_case.json", "r") as f:
    medical_cases = json.load(f)

instruction = "You are a medical expert. You are given a doctor's vignette and your job is to generate the 10 most probably diagnoses in this scenario."
formatted_data = []

for case in medical_cases:
    vignette = case["doctor_vignette"]
    formatted_data.append(
        {
            "messages": [
                {"role": "system", "content": instruction},
                {"role": "user", "content": f"Doctor's Vignette: {vignette}"},
            ]
        }
    )

# Convert to Hugging Face Dataset
dataset = Dataset.from_list(formatted_data)

# Step 2: PPO Configuration
ppo_config = PPOConfig(
    learning_rate=1.41e-5,
    batch_size=1,
    mini_batch_size=1,
    gradient_accumulation_steps=4,
)

# Step 3: Load SFT model with value head
sft_model_name = (
    "CodCodingCode/llama-medical-diagnosis"  # Replace with your actual SFT model name
)
print(f"🧠 Loading SFT model: {sft_model_name}")
tokenizer = AutoTokenizer.from_pretrained(sft_model_name)
model = AutoModelForCausalLMWithValueHead.from_pretrained(sft_model_name).to("cuda")

# Step 4: Load reward model
reward_model_name = "meta-llama/Llama-3.1-8B-Instruct"
print(f"🏅 Loading reward model: {reward_model_name}")
reward_tokenizer = AutoTokenizer.from_pretrained(reward_model_name)
reward_model = AutoModelForCausalLM.from_pretrained(reward_model_name).to("cuda")
reward_model.eval()

# Step 5: PPO Trainer
ppo_trainer = PPOTrainer(config=ppo_config, model=model, tokenizer=tokenizer)


# Step 6: Reward function
def get_reward(prompt, response):
    with torch.no_grad():
        inputs = reward_tokenizer(prompt + response, return_tensors="pt").to("cuda")
        output = reward_model(**inputs)
        return output.logits[:, -1].mean().item()


# Step 7: PPO training loop
print("🚀 Starting PPO training loop...")
for sample in dataset:
    system_msg = sample["messages"][0]["content"]
    user_msg = sample["messages"][1]["content"]
    prompt = f"<|system|>\n{system_msg}\n<|user|>\n{user_msg}\n<|assistant|>\n"

    input_ids = tokenizer(prompt, return_tensors="pt").input_ids.to("cuda")
    generated_ids = model.generate(input_ids, max_new_tokens=64)
    response = tokenizer.decode(generated_ids[0], skip_special_tokens=True).replace(
        prompt, ""
    )

    reward = get_reward(prompt, response)
    ppo_trainer.step([prompt], [response], [reward])

# Step 8: Save outputs
print("💾 Saving final PPO-finetuned model...")
ppo_trainer.model.save_pretrained("ppo-finetuned-model")
tokenizer.save_pretrained("ppo-finetuned-model")
print("✅ Done. Model saved to 'ppo-finetuned-model'")

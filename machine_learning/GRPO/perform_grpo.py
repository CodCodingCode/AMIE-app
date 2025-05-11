import os
import torch
import json
import gc
from transformers import AutoTokenizer, GenerationConfig
from transformers import BitsAndBytesConfig
from trl import AutoModelForCausalLMWithValueHead, PPOConfig, PPOTrainer
from peft import PeftModel

# 1) Cleanup
gc.collect()
torch.cuda.empty_cache()
if not torch.cuda.is_available():
    raise EnvironmentError("No GPU available for PPO training")

device = "cuda"

# 2) Load tokenizer and PPO-ready policy
model_dir = "./ppo_ready_output"

tokenizer = AutoTokenizer.from_pretrained(model_dir, use_fast=False)
# ensure pad_token_id is set
tokenizer.pad_token_id = tokenizer.pad_token_id or tokenizer.eos_token_id

# 3) Load base with value head and attach LoRA adapter
#    then re-quantize base to 4-bit for inference/training
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_use_double_quant=True,
    bnb_4bit_compute_dtype=torch.float16,
)

# base for policy
base = AutoModelForCausalLMWithValueHead.from_pretrained(
    "aaditya/Llama3-OpenBioLLM-8B",
    quantization_config=bnb_config,
    device_map="auto",
    torch_dtype=torch.float16,
)
# attach adapter
policy = PeftModel.from_pretrained(base, model_dir, device_map="auto")
policy.generation_config = GenerationConfig(**policy.config.to_dict())
policy.eval()

# 4) Load frozen reference model (no LoRA)
ref_base = AutoModelForCausalLMWithValueHead.from_pretrained(
    "aaditya/Llama3-OpenBioLLM-8B",
    quantization_config=bnb_config,
    device_map={"": "cpu"},
    torch_dtype=torch.float16,
)
ref = ref_base.eval()
ref.generation_config = policy.generation_config

# 5) Reward model (could be same as reference or custom)
reward_model = AutoModelForCausalLMWithValueHead.from_pretrained(
    "aaditya/Llama3-OpenBioLLM-8B",
    quantization_config=bnb_config,
    device_map={"": "cpu"},
    torch_dtype=torch.float16,
).eval()
reward_tok = tokenizer

def get_reward(query: str, response: str) -> float:
    inputs = reward_tok(query + response, return_tensors="pt", truncation=True, max_length=1024)
    with torch.no_grad():
        logits = reward_model(**inputs).logits
    # use average next-token logit as reward proxy
    return float(logits[:, -1].mean())

# 6) Prepare PPO data: a list of prompts
# Replace this with your real prompt list or dataset loader
prompts = [
    "Patient has a fever and cough, what question do you ask?",
    # ... add more prompts
]

# 7) Configure and initialize PPOTrainer
ppo_config = PPOConfig(
    learning_rate=1e-5,
    batch_size=1,
    mini_batch_size=1,
)

ppo_trainer = PPOTrainer(
    ppo_config,
    tokenizer,
    policy,
    ref,
    reward_model,
    prompts,
    policy,  # reuse value head on policy
)

# 8) Run PPO loop
for prompt in prompts:
    # generate a response
    inputs = tokenizer(prompt, return_tensors="pt").to(device)
    gen_ids = policy.generate(
        **inputs,
        max_new_tokens=64,
        pad_token_id=tokenizer.pad_token_id,
    )
    response = tokenizer.decode(gen_ids[0][inputs.input_ids.shape[-1]:], skip_special_tokens=True)

    # compute reward
    r = get_reward(prompt, response)
    print(f"Prompt: {prompt}\nResponse: {response}\nReward: {r}\n")

    # step PPO
    ppo_trainer.step([prompt], [response], [r])

# 9) Save fine-tuned policy
policy.save_pretrained("./ppo_finetuned_policy")
print("✅ PPO-finetuned policy saved to ./ppo_finetuned_policy")

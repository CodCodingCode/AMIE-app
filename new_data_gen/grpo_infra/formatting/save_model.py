from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

# point to your fine-tuned folder
SAVE_DIR = "llama-3.1-8b-think-answer-debug"

tokenizer = AutoTokenizer.from_pretrained(SAVE_DIR, use_fast=True)
model = AutoModelForCausalLM.from_pretrained(
    SAVE_DIR,
    device_map="auto",
    torch_dtype=torch.bfloat16,  # or float16/float32 as desired
)

# example inference
prompt = "Thinking: What's the cause of a persistent cough?\nAnswer:"
inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
outputs = model.generate(**inputs, max_new_tokens=64, do_sample=False)
print(tokenizer.decode(outputs[0], skip_special_tokens=True))

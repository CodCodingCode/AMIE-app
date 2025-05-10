from transformers import AutoTokenizer, AutoModelForCausalLM

# Replace with your Hugging Face username and repository name
repo_id = "CodCodingCode/llama-medical-diagnosis"

# Load the tokenizer and model
tokenizer = AutoTokenizer.from_pretrained(repo_id)
model = AutoModelForCausalLM.from_pretrained(repo_id)

# Move the model to the appropriate device (CPU or GPU)
import torch
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = model.to(device)

# Test the model with a sample input
test_text = "I have back pain and fever. What could be the diagnosis?"
inputs = tokenizer(test_text, return_tensors="pt").to(device)

# Generate a response
with torch.no_grad():
    outputs = model.generate(
        **inputs,
        max_new_tokens=200,
        temperature=0.7,
        do_sample=True,
        pad_token_id=tokenizer.eos_token_id,
    )

# Decode and print the response
response = tokenizer.decode(outputs[0], skip_special_tokens=True)
print(f"Prompt: {test_text}\nResponse: {response}")
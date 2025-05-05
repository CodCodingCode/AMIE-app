from transformers import AutoModelForCausalLM, AutoTokenizer

# Load the model and tokenizer
model_name = "aaditya/Llama3-OpenBioLLM-8B"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)

# Format the input properly for Llama models - simplified prompt format
input_text = """<|system|>
You are a helpful medical assistant. When asked about symptoms, you provide a list of potential diagnoses.
<|user|>
I have a cold, and a sore throat. What disease do you think I have? Provide a top 10 diagnosis.
<|assistant|>"""

# Tokenize input
inputs = tokenizer(input_text, return_tensors="pt")

# Use CPU instead of MPS to avoid potential issues
device = "cpu"
model = model.to(device)
inputs = {k: v.to(device) for k, v in inputs.items()}

# Generate output with modified parameters
outputs = model.generate(
    **inputs,
    max_new_tokens=256,  # Reduced from 512 to speed up generation
    temperature=0.9,  # Increased for more creativity
    top_p=0.95,  # Slightly increased
    do_sample=True,
    repetition_penalty=1.2,  # Added to reduce repetitions
    pad_token_id=tokenizer.eos_token_id
)

# Get original input length to trim it from output
input_length = inputs["input_ids"].shape[
    1
]  # Fixed: access input_ids from the dictionary

# Extract only the generated text (not the input prompt)
generated_tokens = outputs[0][input_length:]
response = tokenizer.decode(generated_tokens, skip_special_tokens=True)

print("MODEL RESPONSE:")
print(response)

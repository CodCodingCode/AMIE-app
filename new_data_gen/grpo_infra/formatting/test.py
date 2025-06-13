from transformers import AutoTokenizer, AutoModelForCausalLM

model_id = "CodCodingCode/llama-3.1-8b-grpo-v1.2"

# Load tokenizer and model
tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    device_map="auto",  # or "cuda:0" if you use one GPU
    torch_dtype="auto",  # uses fp16 if possible
)

# Create a sample input
input_text = """

Instruction: You are a clinical summarizer. Given a transcript of a doctor–patient dialogue, extract a structured clinical vignette summarizing the key symptoms, relevant history, and any diagnostic clues.
Input: I am 14. I am a male. I have pain in my knee. 
Output: THINKING: 
"""

# Tokenize and generate
inputs = tokenizer(input_text, return_tensors="pt").to(model.device)
outputs = model.generate(**inputs, max_new_tokens=400)

# Decode and print
print(tokenizer.decode(outputs[0], skip_special_tokens=True))

input_text2 = f"""
Instruction: You are a diagnostic reasoning model. Given the current vignette, prior dialogue, and diagnostic hypothesis, refine the list of possible diagnoses with concise justifications for each. Aim to reduce diagnostic uncertainty.
Input: {input_text}
Output: THINKING:
"""
inputs = tokenizer(input_text2, return_tensors="pt").to(model.device)
outputs = model.generate(**inputs, max_new_tokens=400)

# Decode and print
print(tokenizer.decode(outputs[0], skip_special_tokens=True))

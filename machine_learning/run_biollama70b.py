import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

# Configure 4-bit quantization
quantization_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_quant_type="nf4",  # Normal Float 4-bit - better quality than fp4
    bnb_4bit_use_double_quant=True  # Nested quantization for further memory savings
)

# Load tokenizer
tokenizer = AutoTokenizer.from_pretrained("aaditya/Llama3-OpenBioLLM-70B")

# Load model in 4-bit with additional memory optimizations
model = AutoModelForCausalLM.from_pretrained(
    "aaditya/Llama3-OpenBioLLM-70B",
    device_map="auto",  # Automatically distribute layers based on available memory
    quantization_config=quantization_config,
    offload_folder="offload_folder",  # Offload to disk if needed
    torch_dtype=torch.float16,  # Use half precision for non-quantized parts
)

# Format the input properly for Llama models
input_text = """<|system|>
You are a helpful medical assistant. When asked about symptoms, you provide a list of potential diagnoses.
<|user|>
I have a cold, and a sore throat. What disease do you think I have? Provide a top 10 diagnosis.
<|assistant|>"""

# Tokenize input
inputs = tokenizer(input_text, return_tensors="pt").to('auto')

# Generate output with modified parameters
outputs = model.generate(
    **inputs,
    max_new_tokens=256,
    temperature=0.7,
    top_p=0.95,
    do_sample=True,
    repetition_penalty=1.2,
    pad_token_id=tokenizer.eos_token_id
)

# Decode and print the output
response = tokenizer.decode(outputs[0], skip_special_tokens=True)
print(response)
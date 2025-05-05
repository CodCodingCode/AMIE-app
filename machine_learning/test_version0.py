import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
import gc

# --- Configuration ---
base_model_name = "aaditya/Llama3-OpenBioLLM-8B"
adapter_path = "CodCodingCode/Llama3-OpenBioLLM-8B-4bit-peft-adapter-test"

# --- Device Setup ---
device = "cpu"  # Force CPU since bitsandbytes won't work
print("Warning: Running on CPU. This will be very slow.")
# No need to clear GPU cache
gc.collect()

# --- Load Base Model (NO Quantization) ---
print(f"Loading base model: {base_model_name} (NO quantization)...")

base_model = AutoModelForCausalLM.from_pretrained(
    base_model_name,
    device_map=None,  # Load directly to CPU
    torch_dtype=torch.float32,  # Use standard float32 on CPU
    trust_remote_code=True,
    low_cpu_mem_usage=False,  # May need more RAM now
)
print("Base model loaded.")

# --- Load Tokenizer ---
# Load tokenizer associated with the adapter or base model
# If you saved the tokenizer with the adapter, loading from adapter_path is safer
try:
    tokenizer = AutoTokenizer.from_pretrained(adapter_path, trust_remote_code=True)
    print(f"Tokenizer loaded from adapter path: {adapter_path}")
except Exception as e:
    print(
        f"Could not load tokenizer from adapter path ({e}). Loading from base model path: {base_model_name}"
    )
    tokenizer = AutoTokenizer.from_pretrained(base_model_name, trust_remote_code=True)

if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token
    print("Set pad_token to eos_token")

# --- Load PEFT Adapter ---
print(f"Loading PEFT adapter from: {adapter_path}...")
# Load adapter onto the base model (which is now on CPU)
model = PeftModel.from_pretrained(base_model, adapter_path)
print("PEFT adapter loaded and applied.")

# --- Inference ---
model.eval()  # Set model to evaluation mode
model.to(device)  # Ensure the final PEFT model is on the CPU


def generate_response(prompt):
    """Generates a response from the model given a prompt."""
    print(f"\nPrompt: {prompt}")
    # Ensure inputs are on the CPU
    inputs = tokenizer(prompt, return_tensors="pt").to(device)

    print("Generating response...")
    with torch.no_grad():  # Disable gradient calculations for inference
        outputs = model.generate(
            **inputs,
            max_new_tokens=100,  # Adjust max length as needed
            num_return_sequences=1,
            temperature=0.7,  # Adjust temperature for creativity vs. determinism
            do_sample=True,  # Use sampling for more varied responses
            pad_token_id=tokenizer.eos_token_id,
            eos_token_id=tokenizer.eos_token_id,
        )

    # Decode the generated tokens, skipping special tokens and the prompt itself
    response_ids = outputs[0][
        inputs.input_ids.shape[1] :
    ]  # Get only the newly generated tokens
    response = tokenizer.decode(response_ids, skip_special_tokens=True)

    print(f"Response: {response.strip()}")
    return response.strip()


# --- Test Prompts ---
test_prompt_1 = "What is the diagnosis for a patient with severe fatigue, joint pain, and butterfly rash on the face?"
test_prompt_2 = "Summarize the key differences between Type 1 and Type 2 diabetes."
test_prompt_3 = "Patient presents with sudden onset chest pain radiating to the left arm. What are the immediate steps?"
# Add more relevant medical prompts here

generate_response(test_prompt_1)
generate_response(test_prompt_2)
generate_response(test_prompt_3)

print("\nTesting finished.")

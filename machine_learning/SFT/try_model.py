from transformers import AutoTokenizer, BitsAndBytesConfig, AutoModelForCausalLM
from peft import PeftModel
import torch

# ── 1) Define your repos ─────────────────────────────────────────
ADAPTER_REPO = (
    "CodCodingCode/DeepSeek-V2-medical"  # where your adapter + tokenizer live
)
BASE_MODEL = "deepseek-ai/DeepSeek-V2-Lite"  # the 4-bit base you used

# ── 2) Load the tokenizer you saved (pulls from ADAPTER_REPO) ──
tokenizer = AutoTokenizer.from_pretrained(
    ADAPTER_REPO,
    trust_remote_code=True,
)
# ensure padding is set
tokenizer.pad_token_id = tokenizer.pad_token_id or tokenizer.eos_token_id

# ── 3) Reload the base quantized model ──────────────────────────
bnb = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16,  # or torch.float16
)
base = AutoModelForCausalLM.from_pretrained(
    BASE_MODEL,
    quantization_config=bnb,
    device_map="auto",
    trust_remote_code=True,
)
# resize its embeddings to match YOUR tokenizer’s vocab
base.resize_token_embeddings(len(tokenizer))

# ── 4) Attach your LoRA adapter from the Hub repo ──────────────
model = PeftModel.from_pretrained(
    base,
    ADAPTER_REPO,
    device_map="auto",
    trust_remote_code=True,
)
model.config.use_cache = True  # for faster generation

# ── 5) Generate! ────────────────────────────────────────────────
prompt = "How would you treat a patient with a suspected case of COVID-19?"
inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

# you can now use `.generate()` normally
output_ids = model.generate(
    **inputs,
    max_new_tokens=64,
    do_sample=True,
    temperature=0.2,
    top_p=0.95,
    pad_token_id=tokenizer.pad_token_id,
    eos_token_id=tokenizer.eos_token_id,
)
print(tokenizer.decode(output_ids[0], skip_special_tokens=True))

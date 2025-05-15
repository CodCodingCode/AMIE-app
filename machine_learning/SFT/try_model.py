import torch
from transformers import (
    AutoTokenizer,
    GenerationConfig,
    BitsAndBytesConfig,
)
from trl import AutoModelForCausalLMWithValueHead
from peft import PeftModel
from transformers.generation.utils import DynamicCache

# ───── Monkey-patch the buggy cache method ─────
DynamicCache.get_max_length = DynamicCache.get_seq_length

ADAPTER_REPO = "CodCodingCode/DeepSeek-V2-med"
BASE_ID      = "deepseek-ai/DeepSeek-V2-Lite"

# ───── Load tokenizer ─────
tokenizer = AutoTokenizer.from_pretrained(
    ADAPTER_REPO, use_fast=False, trust_remote_code=True
)
tokenizer.pad_token_id = tokenizer.eos_token_id

# ───── Reload quantized value-head base ─────
bnb = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_use_double_quant=True,
    bnb_4bit_compute_dtype=torch.float16,
)
base = AutoModelForCausalLMWithValueHead.from_pretrained(
    BASE_ID,
    quantization_config=bnb,
    device_map="auto",
    trust_remote_code=True,
)
base.config.use_cache = False

# ───── Attach LoRA adapter ─────
model = PeftModel.from_pretrained(
    base,
    ADAPTER_REPO,
    device_map="auto",
    torch_dtype=torch.float16,
    trust_remote_code=True,
)
model.config.use_cache = False

# ───── GenerationConfig on the underlying base ─────
model.base_model.generation_config = GenerationConfig(
    max_new_tokens=64,
    do_sample=True,
    temperature=0.2,
    top_p=0.95,
    repetition_penalty=1.1,
    no_repeat_ngram_size=3,
    eos_token_id=tokenizer.eos_token_id,
    pad_token_id=tokenizer.pad_token_id,
    use_cache=False,
)

device = next(model.parameters()).device
prompt = "How would you treat a patient with a suspected case of COVID-19? " \


# … after you’ve done:
inputs = tokenizer(prompt, return_tensors="pt").to(device)

# 1) grab the last token column (shape [B,1])
last_ids   = inputs.input_ids[:, -1:]
last_mask  = inputs.attention_mask[:, -1:]

# 2) concatenate to make length = S+1 for both tensors
inputs.input_ids      = torch.cat([inputs.input_ids,      last_ids],  dim=1)
inputs.attention_mask = torch.cat([inputs.attention_mask, last_mask], dim=1)

# 3) now call generate, passing both tensors
with torch.no_grad():
    out_ids = model.generate(
        input_ids=inputs.input_ids,
        attention_mask=inputs.attention_mask,
        max_new_tokens=64,
        do_sample=True,
        top_p=0.95,
        temperature=0.2,
        eos_token_id=tokenizer.eos_token_id,
        pad_token_id=tokenizer.pad_token_id,
        use_cache=False,         # disable the broken cache path
    )

# 4) strip off your prompt tokens, decode only the new bits
prompt_len = inputs.input_ids.shape[-1]
new_tokens = out_ids[0, prompt_len:]
print(tokenizer.decode(new_tokens, skip_special_tokens=True))

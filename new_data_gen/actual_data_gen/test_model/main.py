from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel
import torch

# 1. Base model (DeepSeek V2 Lite)
base_model_id = "deepseek-ai/DeepSeek-V2-Lite"
tokenizer = AutoTokenizer.from_pretrained(base_model_id)
base_model = AutoModelForCausalLM.from_pretrained(
    base_model_id,
    torch_dtype=torch.float16,
    device_map="auto",  # Or .to("cuda") if you're not using multiple GPUs
)

# 2. Load the LoRA adapter on top of the base model
adapter_model_id = "CodCodingCode/DeepSeek-V2-medical"
model = PeftModel.from_pretrained(base_model, adapter_model_id)

instruction = "You are a physician asking questions to diagnose a patient."

input_text = "THINKING: The patient presents with pain in the left leg, which appears twisted or turned outward. There is no numbness or tingling reported, which may suggest that there is no significant nerve injury or compression. The twisting or outward turning of the leg is a classic presentation for hip injury, particularly hip dislocation or fracture. Hip fractures often present with the leg shortened and externally rotated; hip dislocations can cause similar deformities and pain.\n\nAlternative diagnoses could include:\n- Femoral shaft fracture: This can cause deformity and pain but usually results in more obvious limb shortening and sometimes neurovascular compromise.\n- Knee or ankle injury: These might cause deformity of the limb but the twisting at the hip level would be less likely.\n- Pelvic fracture: May cause hip pain but often with other signs such as instability or pelvic tenderness.\n- Muscle or ligament injury around the hip: Would be less likely to cause the leg to appear twisted or rotated.\n\nSince the description of the leg being twisted outward and painful highly aligns with an injury to the hip, especially a hip fracture or dislocation, the gold-standard diagnosis given (injury to the hip) is well supported by the vignette.\n\nChecklist:\n- Does the vignette fully support the gold label? Yes.\n- Is there no meaningful diagnostic uncertainty remaining? Yes, presenting features strongly suggest hip injury.\n- Has the conversation had at least 8 total turns (excluding summaries)? No, currently only 2 turns.\n- Is any further clarification, lab, or follow-up unnecessary? Based on the information given, no further clarification is necessary for the diagnosis.\n\nI will await further information or more turns before concluding definitively. For now, working impression is injury to the hip, consistent with the gold standard.\n\nANSWER: Injury to the hip"

full_prompt = (
    f"### Instruction:\n{instruction}\n\n"
    f"### Input:\n{input_text}\n\n"
    f"### Response:\n"
)

# 2️⃣ run the text-generation pipeline
# 4. Tokenization & Generation
inputs = tokenizer(full_prompt, return_tensors="pt").to("cuda")

with torch.no_grad():
    outputs = model.generate(
        **inputs, max_new_tokens=256, temperature=0.2, top_p=0.95, do_sample=True
    )

# 5. Decode and print the output
response = tokenizer.decode(outputs[0], skip_special_tokens=True)
print(response)

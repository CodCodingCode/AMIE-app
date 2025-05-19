import os
import json
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel, PeftConfig
import torch

# === Load Adapter-based Model ===
adapter_model_id = "CodCodingCode/DeepSeek-V2-medical"
config = PeftConfig.from_pretrained(adapter_model_id)

base_model = AutoModelForCausalLM.from_pretrained(
    config.base_model_name_or_path, torch_dtype=torch.float16, device_map="auto"
)
model = PeftModel.from_pretrained(base_model, adapter_model_id)
tokenizer = AutoTokenizer.from_pretrained(config.base_model_name_or_path)


class RoleResponder:
    def __init__(self, role_instruction):
        self.role_instruction = role_instruction

    def ask(self, user_input):
        prompt = f"""
        instruction: {self.role_instruction}
        input: {user_input}
        output:
        """
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        outputs = model.generate(
            **inputs, max_new_tokens=300, do_sample=True, temperature=0.7
        )
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        return response.split("DOCTOR:")[-1].strip()


# === Example Setup ===
summarizer = RoleResponder(
    "You are a clinical summarizer trained to extract structured vignettes from patient descriptions."
)
diagnoser = RoleResponder(
    "You are a board-certified diagnostician attempting to understand a patient's condition."
)
questioner = RoleResponder(
    "You are a doctor asking the patient questions to clarify the diagnosis."
)


def simulate_doctor_interaction(user_input):
    print("👤 PATIENT (You):", user_input)

    # Step 1: Doctor initial response
    doctor_reply = diagnoser.ask(user_input)
    print("🩺 DOCTOR:", doctor_reply)

    # Step 2: Summarize current vignette
    vignette_summary = summarizer.ask(user_input + "\n" + doctor_reply)
    print("🧾 VIGNETTE SUMMARY:", vignette_summary)

    # Step 3: Doctor asks follow-up
    follow_up_question = questioner.ask(vignette_summary)
    print("❓ DOCTOR FOLLOW-UP:", follow_up_question)


# === Run an example ===
if __name__ == "__main__":
    user_input = input("🩺 What brings you in today: ")
    simulate_doctor_interaction(user_input)

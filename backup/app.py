import os
import torch
from huggingface_hub import snapshot_download
from transformers import AutoTokenizer, AutoModelForCausalLM
import gradio as gr

# ——— CONFIG ———  
REPO_ID   = "CodCodingCode/llama-3.1-8b-clinical"  
SUBFOLDER = "checkpoint-45000"  
HF_TOKEN  = os.environ["HUGGINGFACE_HUB_TOKEN"]  # set in Settings→Secrets  

# ——— SNAPSHOT & LOAD ———  
# This will grab all .json and .safetensors under checkpoint-45000:
local_dir = snapshot_download(
    repo_id=REPO_ID,
    subfolder=SUBFOLDER,
    token=HF_TOKEN,
    allow_patterns=["*.json", "*.safetensors"],
)

# Now point at that folder:
MODEL_DIR = local_dir  # e.g. ~/.cache/huggingface/…/checkpoint-45000

# Load tokenizer & model from the real files you just pulled:
tokenizer = AutoTokenizer.from_pretrained(
    MODEL_DIR,
    use_fast=False,
    trust_remote_code=True,
)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_DIR,
    device_map="auto",
    torch_dtype=torch.float16,
    trust_remote_code=True,
)
model.eval()



# === Role Agent with instruction/input/output format ===
class RoleAgent:
    def __init__(self, role_instruction):
        self.role_instruction = role_instruction

    def act(self, input_text):
        prompt = (
            f"Instruction: {self.role_instruction}\n"
            f"Input: {input_text}\n"
            f"Output:"
        )
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        outputs = model.generate(
            **inputs,
            max_new_tokens=256,
            do_sample=True,
            temperature=0.7,
            pad_token_id=tokenizer.eos_token_id,
        )
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)

        # extract THINKING / ANSWER if present
        thinking, answer = "", response
        if "THINKING:" in response and "ANSWER:" in response and "END" in response:
            block = response.split("THINKING:")[1].split("END")[0]
            thinking = block.split("ANSWER:")[0].strip()
            answer = block.split("ANSWER:")[1].strip()

        return {
            "instruction": f"You are {self.role_instruction}.",
            "input": input_text,
            "thinking": thinking,
            "output": answer,
        }


# === Agents ===
summarizer = RoleAgent(
    "You are a clinical summarizer trained to extract structured vignettes from doctor–patient dialogues."
)
diagnoser = RoleAgent(
    "You are a board-certified diagnostician that diagnoses patients."
)
questioner = RoleAgent("You are a physician asking questions to diagnose a patient.")

treatment_agent = RoleAgent(
    "You are a board-certified clinician. Based on the diagnosis and patient vignette provided below, suggest a concise treatment plan that could realistically be initiated by a primary care physician or psychiatrist."
)


# === Inference State ===
conversation_history = []
summary = ""
diagnosis = ""


# === Gradio Inference ===
def simulate_interaction(user_input, iterations=1):
    history = [f"Doctor: What brings you in today?", f"Patient: {user_input}"]
    summary, diagnosis = "", ""

    for i in range(iterations):
        # Summarize
        sum_in = "\n".join(history) + f"\nPrevious Vignette: {summary}"
        sum_out = summarizer.act(sum_in)
        summary = sum_out["output"]

        # Diagnose
        diag_out = diagnoser.act(summary)
        diagnosis = diag_out["output"]

        # Question
        q_in = f"Vignette: {summary}\nCurrent Estimated Diagnosis: {diag_out['thinking']} {diagnosis}"
        q_out = questioner.act(q_in)
        history.append(f"Doctor: {q_out['output']}")
        history.append("Patient: (awaiting response)")

        # Treatment
        treatment_out = treatment_agent.act(
            f"Diagnosis: {diagnosis}\nVignette: {summary}"
        )

        return {
            "summary": sum_out,
            "diagnosis": diag_out,
            "question": q_out,
            "treatment": treatment_out,
            "conversation": "\n".join(history),
        }


# === Gradio UI ===
def ui_fn(user_input):
    res = simulate_interaction(user_input)
    return f"""📋 Vignette Summary:
💭 THINKING: {res['summary']['thinking']}
ANSWER: {res['summary']['output']}

🩺 Diagnosis:
💭 THINKING: {res['diagnosis']['thinking']}
ANSWER: {res['diagnosis']['output']}
T
❓ Follow-up Question:
💭 THINKING: {res['question']['thinking']}
ANSWER: {res['question']['output']}

💊 Treatment Plan:
{res['treatment']['output']}

💬 Conversation:
{res['conversation']}
"""


demo = gr.Interface(
    fn=ui_fn,
    inputs=gr.Textbox(label="Patient Response"),
    outputs=gr.Textbox(label="Doctor Simulation Output"),
    title="🧠 AI Doctor Multi-Agent Reasoning",
)

if __name__ == "__main__":
    demo.launch(share=True)

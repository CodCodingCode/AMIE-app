import json
from openai import OpenAI
import time

# Load JSON list of vignettes
with open("patient_vignette.json", "r") as f:
    vignette_list = json.load(f)

# Initialize OpenAI client
client = OpenAI(api_key=key)
model = "gpt-4.1-mini"

# === NEW: Role Responder Class ===
class RoleResponder:
    def __init__(self, role):
        self.role = role

    def format(self, prompt):
        return f"{self.role}. {prompt} PLEASE FIRST OUTPUT YOUR REASONING using: THINKING: <your reasoning> and then output your answer using: ANSWER: <your answer>"

    def ask(self, user_input):
        messages = [
            {"role": "system", "content": self.format(user_input)},
            {"role": "user", "content": user_input},
        ]
        response = client.chat.completions.create(model=model, messages=messages)
        return response.choices[0].message.content.strip()
    
# === Use the Class for Roles ===
patient = RoleResponder("You are a patient continuing a conversation with your doctor")
summarizer = RoleResponder("You are a clinical summarizer. Convert the conversational chain into a clean medical vignette and explain any reasoning you infer")
diagnoser = RoleResponder("You are a physician. Given this vignette, provide your most likely diagnosis and explain your reasoning")
questioner = RoleResponder("You are a physician. Ask the next best question to refine your diagnosis and explain why")

# === Store all transcripts ===
summarizer_outputs = []
diagnosing_doctor_outputs = []
questioning_doctor_outputs = []
patient_response = []
conversation = []

# === Loop over each vignette ===
for idx, vignette_text in enumerate(vignette_list):
    if idx == 0:
        initial_prompt = "What brings you in today?"
        patient_history = vignette_text
        patient_reply_messages = [
            {
                "role": "system",
                "content": f"You are a patient continuing a conversation with your doctor.",
            },
            {
                "role": "user",
                "content": f"{vignette_text}. Reply realistically to their follow-up question: {initial_prompt}. PLEASE FIRST OUTPUT YOUR REASONING using: THINKING: <your reasoning> and then output your answer using: ANSWER: <your answer>",
            },
        ]

        conversation.append(f"DOCTOR: {initial_prompt}")

        patient_response = patient.ask(f"{vignette_text}. Reply realistically to their follow-up question: {initial_prompt}")
        print("🗣️ Patient's Reply:", patient_followup)
        conversation.append(f"PATIENT: {patient_response}")
        continue

    summarizer_messages = [
        {
            "role": "system",
            "content": f"You are a clinical summarizer. Convert the conversational chain into a clean medical vignette and explain any reasoning you infer. Here is the converation: {conversation}. PLEASE FIRST OUTPUT YOUR REASONING using: THINKING: <your reasoning> and then output your answer using: ANSWER: <your answer>",
        },
        {"role": "user", "content": f"Patient statement:\n{patient_response}"},
    ]
    vignette_summary = summarizer.ask(f"Here is the converation: {conversation}")
    print("🧾 Vignette:", vignette_summary)
    summarizer_outputs.append(
        {"vignette_index": idx, "input": patient_response, "output": vignette_summary}
    )

    # Step 3: Diagnosis
    diagnosis_messages = [
        {
            "role": "system",
            "content": "You are a physician. Given this vignette, provide your most likely diagnosis and explain your reasoning. PLEASE FIRST OUTPUT YOUR REASONING using: THINKING: <your reasoning> and then output your answer using: ANSWER: <your answer>",
        },
        {"role": "user", "content": vignette_summary},
    ]
    diagnosis = diagnoser.ask(vignette_summary)
    print("🔍 Diagnosis:", diagnosis)
    diagnosing_doctor_outputs.append(
        {"vignette_index": idx, "input": vignette_summary, "output": diagnosis}
    )

    # Step 4: Ask follow-up
    question_messages = [
        {
            "role": "system",
            "content": "You are a physician. Ask the next best question to refine your diagnosis and explain why. PLEASE FIRST OUTPUT YOUR REASONING using: THINKING: <your reasoning> and then output your answer using: ANSWER: <your answer>",
        },
        {
            "role": "user",
            "content": f"Vignette:\n{vignette_summary}\n Diagnosis: {diagnosis} PLEASE FIRST OUTPUT YOUR REASONING using: THINKING: <your reasoning> and then output your answer using: ANSWER: <your answer>",
        },
    ]
    followup_question = questioner.ask(f"Vignette:\n{vignette_summary}\nDiagnosis: {diagnosis}")
    print("❓ Follow-up:", followup_question)
    questioning_doctor_outputs.append(
        {"vignette_index": idx, "input": diagnosis, "output": followup_question}
    )
    conversation.append(f"DOCTOR: {followup_question}")

    # Step 5: Patient answers
    patient_followup_messages = [
        {
            "role": "system",
            "content": f"You are a patient continuing a conversation with your doctor.",
        },
        {
            "role": "user",
            "content": f"{vignette_text}. Reply realistically to their follow-up question: {initial_prompt}. PLEASE FIRST OUTPUT YOUR REASONING using: THINKING: <your reasoning> and then output your answer using: ANSWER: <your answer>",
        },
    ]
    patient_followup = patient.ask(f"{vignette_text}. Reply realistically to their follow-up question: {initial_prompt}")
    print("🗣️ Patient:", patient_followup)
    conversation.append(f"PATIENT: {patient_response}")
    patient_response.append(
        {
            "vignette_index": idx,
            "input": vignette_text + followup_question,
            "output": patient_followup,
        }
    )

    time.sleep(1.2)

# === Save role-specific outputs ===
with open("summarizer_outputs.json", "w") as f:
    json.dump(summarizer_outputs, f, indent=2)
with open("diagnosing_doctor_outputs.json", "w") as f:
    json.dump(diagnosing_doctor_outputs, f, indent=2)
with open("questioning_doctor_outputs.json", "w") as f:
    json.dump(questioning_doctor_outputs, f, indent=2)
with open("patient_followups.json", "w") as f:
    json.dump(patient_response, f, indent=2)

print("\n✅ All role outputs saved.")
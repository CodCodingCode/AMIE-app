import json
from openai import OpenAI
import time

# Initialize OpenAI client
client = OpenAI(
    api_key="api-key-here"  # Replace with your actual API key  
)
model = "gpt-4.1-mini"


class RoleResponder:
    def __init__(self, role_instruction):
        self.role_instruction = role_instruction

    def ask(self, user_input):
        messages = [
            {"role": "system", "content": self.role_instruction},
            {
                "role": "user",
                "content": f"{user_input}",
            },
        ]
        response = client.chat.completions.create(model=model, messages=messages)
        return response.choices[0].message.content.strip()


# === Use the Class for Roles ===
patient = RoleResponder(
    "You are simulating a real patient in conversation with their doctor."
)

summarizer = RoleResponder(
    "You are a clinical summarizer trained to extract structured vignettes from doctor–patient dialogues."
)

diagnoser = RoleResponder("You are a board-certified diagnostician.")

questioner = RoleResponder("You are a physician refining your differential diagnosis.")


# === Store all transcripts ===
summarizer_outputs = []
diagnosing_doctor_outputs = []
questioning_doctor_outputs = []
patient_response = []
conversation = []


# === Loop over each vignette ===
def process_vignette(idx, vignette_text):
    global conversation, patient_response, summarizer_outputs, diagnosing_doctor_outputs, questioning_doctor_outputs
    initial_prompt = "What brings you in today?"
    conversation.clear()
    conversation.append(f"DOCTOR: {initial_prompt}")

    raw_patient = patient.ask(
        f"""You are simulating a real patient in conversation with their doctor. 
Respond naturally and realistically, as if you are experiencing symptoms yourself — but like a real patient, you are NOT medically trained and do NOT understand what’s important or what anything means. 
You have NOT spoken to any other doctors. 
You may feel scared, unsure, or even embarrassed. 
You are NOT trying to impress the doctor with a clear answer — just describe what you feel in your own confused way. 

NEVER hallucinate past medical evaluations, tests, or diagnoses. 
Do NOT give clear medical names unless the doctor already told you. 
Don’t jump to conclusions about your condition. 
Be vague, partial, emotional, even contradictory if needed. 
Just say what you're feeling — physically or emotionally — in one or two sentences.

PLEASE OUTPUT YOUR ANWER SIMILAR TO THE FOLLOWING EXAMPLE:

THINKING: <your thinking as a model on how a patient should respond to the doctor.>
ANSWER: <your vague, real-patient-style reply to the doctor>

Patient background: {vignette_text}
Doctor's question: {initial_prompt}"""
    )
    if "ANSWER:" in raw_patient:
        patient_response_text = raw_patient.split("ANSWER:")[1].strip()
    else:
        patient_response_text = raw_patient
    print("🗣️ Patient's Reply:", patient_response_text)
    conversation.append(f"PATIENT: {patient_response_text}")
    turn_count = 0  # Doctor + patient
    diagnosis_complete = False
    prev_vignette_summary = ""

    while not diagnosis_complete:
        joined_conversation = "\\n".join(conversation)
        vignette_summary = summarizer.ask(
            f"""You are a clinical summarizer trained to extract structured vignettes from doctor–patient dialogues.
Your task is to summarize only newly emerged clinical information. If there are no meaningful updates since the previous vignette, respond with:

ANSWER: [No significant update since last summary.]

Otherwise, identify the patient's age, gender (if known), chief complaint, new symptoms, and how the physician's clinical reasoning has evolved based on the most recent interaction.

THINKING: <summarizer reasoning about whether clinical content changed and how>. 
ANSWER: <updated vignette summary, or indicate 'No significant update'>.

Latest conversation:
{joined_conversation}

Previous vignette summary:
{prev_vignette_summary}
"""
        )
        print("🧾 Vignette:", vignette_summary)
        summarizer_outputs.append(
            {
                "vignette_index": idx,
                "input": patient_response_text,
                "output": vignette_summary,
            }
        )

        with open("summarizer_outputs.json", "w") as f:
            json.dump(summarizer_outputs, f, indent=2)

        prev_vignette_summary = vignette_summary

        if "ANSWER:" in vignette_summary:
            vignette_summary = vignette_summary.split("ANSWER:")[1].strip()
        else:
            vignette_summary = vignette_summary

        # Step 3: Diagnosis
        diagnosis = diagnoser.ask(
            f"""You are a board-certified diagnostician. Given the vignette, simulate how you would reason through the diagnosis in a real clinical setting. 
    List the most possible condition, justify it with supporting symptoms and findings, and explain why less likely options can be ruled out. 

    THINKING: <your step-by-step diagnostic reasoning, including uncertainties>. GIVE ALL THINKING HERE
    ANSWER: <your final diagnosis>. GIVE NO OTHER INFORMATION OTHER THAN THE FINAL DIAGNOSIS

    End your response by clearly stating END (exactly like END with the capitalization and all) ONLY IF:
    1. You are extremely confident in a **single specific diagnosis**, AND
    2. There is **no meaningful diagnostic uncertainty remaining**, AND
    3. At least 10 conversation turns have occurred (not including summarizer turns), AND
    4. No further testing, clarification, or follow-up is necessary based on the vignette.

    If any of these conditions are NOT met, do NOT write END in ANY PART OF THE OUTPUT. Continue reasoning or request further clarification.

    Vignette:\n{vignette_summary}
    Turn count: {turn_count}"""
        )

        print("Turn count:", turn_count)

        print("🔍 Diagnosis:", diagnosis)
        diagnosing_doctor_outputs.append(
            {"vignette_index": idx, "input": vignette_summary, "output": diagnosis}
        )

        with open("summarizer_outputs.json", "w") as f:
            json.dump(summarizer_outputs, f, indent=2)
        with open("diagnosing_doctor_outputs.json", "w") as f:
            json.dump(diagnosing_doctor_outputs, f, indent=2)

        if "END" in diagnosis and turn_count >= 10:
            print(f"✅ Reached END for vignette {idx}. Moving to next.\n")
            diagnosis_complete = True
            break

        # Limit to last 3–5 doctor questions
        previous_questions = [
            entry.replace("DOCTOR:", "").strip()
            for entry in conversation
            if entry.startswith("DOCTOR:")
        ][-5:]

        # Step 4: Ask follow-up
        raw_followup = raw_followup = questioner.ask(
            f"""You are a physician refining your differential diagnosis. Based on the current case, ask the single most informative NEW question to either confirm or rule out a major possibility.

Previously asked questions: {json.dumps(previous_questions)}

Frame your reasoning in terms of diagnostic value — how would the answer change your thinking?

THINKING: <why this question has high diagnostic yield and what each possible answer would imply>.
ANSWER: <your follow-up question in plain language>

Try to add new information not covered within the vignette. Do NOT repeat the same question or ask for information already provided.

Vignette:\n{vignette_summary}
Current Esimtated Diagnosis: {diagnosis}
"""
        )
        if "ANSWER:" in raw_followup:
            followup_question = raw_followup.split("ANSWER:")[1].strip()
        else:
            followup_question = raw_followup
        print("❓ Follow-up:", followup_question)
        questioning_doctor_outputs.append(
            {"vignette_index": idx, "input": diagnosis, "output": followup_question}
        )
        conversation.append(f"DOCTOR: {followup_question}")

        # Step 5: Patient answers
        raw_patient_fb = patient.ask(
            f"You are simulating a real patient in conversation with their doctor. Respond naturally, as if you are experiencing the symptoms yourself — but like a real patient, you are not medically trained and don’t fully understand what matters. Only mention what *you* feel or notice, even if it's vague or incomplete. Be hesitant, uncertain, or even wrong. Do NOT describe all symptoms clearly unless directly asked. Limit your response to one or two sentences MAX. THINKING: <your internal thoughts, fears, or confusion>. ANSWER: <your spoken reply to the doctor>\n\nPatient background: {vignette_text}\nDoctor's question: {conversation[-1].replace('DOCTOR:', '').strip()}"
        )
        if "ANSWER:" in raw_patient_fb:
            patient_followup_text = raw_patient_fb.split("ANSWER:")[1].strip()
        else:
            patient_followup_text = raw_patient_fb

        print("🗣️ Patient:", patient_followup_text)
        conversation.append(f"PATIENT: {patient_followup_text}")
        patient_response.append(
            {
                "vignette_index": idx,
                "input": vignette_text + followup_question,
                "output": patient_followup_text,
            }
        )

        turn_count += 2

        # === Save role-specific outputs ===
        with open("questioning_doctor_outputs.json", "w") as f:
            json.dump(questioning_doctor_outputs, f, indent=2)
        with open("patient_followups.json", "w") as f:
            json.dump(patient_response, f, indent=2)


# === Load and Flatten JSON ===
with open("dataset_generation/Again/disease_vignettes.json", "r") as f:
    vignette_dict = json.load(f)

flattened_vignettes = []
for disease, vignettes in vignette_dict.items():
    for vignette in vignettes:
        flattened_vignettes.append((disease, vignette))

for idx, (disease, vignette_text) in enumerate(flattened_vignettes):
    process_vignette(idx, vignette_text)

print("\n✅ All role outputs saved.")

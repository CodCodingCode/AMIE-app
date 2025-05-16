import os
import json
from openai import OpenAI
import time
import multiprocessing

# Initialize OpenAI client
client = OpenAI(
    api_key=""
)  # Replace with your actual API key
model = "gpt-4.1-mini"

treatment_plans = []

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
def process_vignette(idx, vignette_text, gold_label):
    global conversation, patient_response, summarizer_outputs, diagnosing_doctor_outputs, questioning_doctor_outputs, treatment_plans
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
    patient_response.append(
        {
            "vignette_index": idx,
            "input": f"{vignette_text}\n{initial_prompt}",
            "output": patient_response_text,
        }
    )
    turn_count = 0  # Doctor + patient
    diagnosis_complete = False
    prev_vignette_summary = ""

    while not diagnosis_complete:
        joined_conversation = "\\n".join(conversation)
        vignette_summary = summarizer.ask(
            f"""You are a clinical summarizer trained to extract structured vignettes from doctor–patient dialogues.

Use the gold diagnosis only to assess whether the patient's reported symptoms are consistent or missing anything important — DO NOT use it to hallucinate or invent new symptoms.

Gold Diagnosis: {gold_label}

Your task is to summarize only newly emerged clinical information. If nothing new has appeared, respond with:
ANSWER: [No significant update since last summary.]

Only summarize confirmed facts explicitly stated by the patient or the doctor. Do not speculate.

THINKING: <Your reasoning about whether the conversation introduced new clinical details>. 
ANSWER: <Newly updated vignette, or indicate no update>.

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

        prev_vignette_summary = vignette_summary

        if "ANSWER:" in vignette_summary:
            vignette_summary = vignette_summary.split("ANSWER:")[1].strip()
        else:
            vignette_summary = vignette_summary

        # Step 3: Diagnosis
        diagnosis = diagnoser.ask(
            f"""You are a board-certified diagnostician.

You are provided the known gold-standard diagnosis for this patient: **{gold_label}**
Use this information as a reference to guide your diagnostic reasoning and see if the presented vignette aligns with this diagnosis — but **do NOT assume it's correct** unless supported by the vignette.

Your job is to:
- Think through alternative plausible diagnoses
- Justify why some are more likely or less likely
- Compare the gold diagnosis to your working impression based on the vignette alone

THINKING: <Your full reasoning, including how closely this matches the gold label or not>.

If you believe the dialogue should end, explicitly confirm each of the following in your THINKING (checklist style):
- Does the vignette fully support the gold label?
- Is there no meaningful diagnostic uncertainty remaining?
- Has the conversation had at least 8 total turns (excluding summaries)?
- Is any further clarification, lab, or follow-up unnecessary?

If all of these are clearly true, you MUST output END after your diagnosis.

ANSWER: <Your most likely diagnosis, or END if all above conditions are met>.

Vignette:\n{vignette_summary}
Turn count: {turn_count}"""
        )

        print("Turn count:", turn_count)

        print("🔍 Diagnosis:", diagnosis)
        diagnosing_doctor_outputs.append(
            {"vignette_index": idx, "input": vignette_summary, "output": diagnosis}
        )

        # Handle END signal explicitly
        if "END" in diagnosis:
            if turn_count >= 8:
                print(f"✅ Reached END for vignette {idx}. Moving to next.\n")
                diagnosis_complete = True
                break
            else:
                print(
                    f"⚠️ Model said END before 10 turns. Ignoring END due to insufficient conversation length."
                )

        # Step 3.5: Generate Treatment Plan
        treatment = diagnoser.ask(
            f"""You are a board-certified clinician. Based on the diagnosis provided below, suggest a concise treatment plan that could realistically be initiated by a primary care physician or psychiatrist.

Diagnosis: {diagnosis}

Include both non-pharmacological and pharmacological interventions if appropriate. Limit your plan to practical, real-world guidance.

Output ONLY the treatment plan. Do not explain your reasoning.
"""
        )
        print("💊 Treatment Plan:", treatment)
        treatment_plans.append(
            {"vignette_index": idx, "input": diagnosis, "output": treatment}
        )

        # Limit to last 3–5 doctor questions
        previous_questions = [
            entry.replace("DOCTOR:", "").strip()
            for entry in conversation
            if entry.startswith("DOCTOR:")
        ][-5:]

        # Step 4: Ask follow-up
        raw_followup = questioner.ask(
            f"""You are a physician refining your differential diagnosis. 

The gold-standard diagnosis is: **{gold_label}**
Use this to avoid redundant or unnecessary questions. 
Ask a NEW question **only if** it would significantly clarify the case or help confirm/rule out {gold_label} in a realistic clinical setting.

Previously asked questions: {json.dumps(previous_questions)}

THINKING: <Why this question adds diagnostic value>.
ANSWER: <Your next question, or say: 'No further useful question available at this point.'>

Vignette:\n{vignette_summary}
Current Estimated Diagnosis: {diagnosis}
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

    with open(f"summarizer_outputs/summarizer_{idx}.json", "w") as f:
        json.dump(summarizer_outputs, f, indent=2)
    with open(f"patient_followups/patient_{idx}.json", "w") as f:
        json.dump(patient_response, f, indent=2)
    with open(f"diagnosing_doctor_outputs/diagnoser_{idx}.json", "w") as f:
        json.dump(diagnosing_doctor_outputs, f, indent=2)
    with open(f"questioning_doctor_outputs/questioner_{idx}.json", "w") as f:
        json.dump(questioning_doctor_outputs, f, indent=2)
    with open(f"treatment_plans/treatment_{idx}.json", "w") as f:
        json.dump(treatment_plans, f, indent=2)

    return {
        "vignette_index": idx,
        "patient_response": patient_response,
        "summarizer_outputs": summarizer_outputs,
        "diagnosing_doctor_outputs": diagnosing_doctor_outputs,
        "questioning_doctor_outputs": questioning_doctor_outputs,
        "treatment_plans": treatment_plans,
    }


def run_vignette_task(args):
    idx, vignette_text, disease = args
    global conversation, patient_response, summarizer_outputs, diagnosing_doctor_outputs, questioning_doctor_outputs, treatment_plans
    conversation = []
    patient_response = []
    summarizer_outputs = []
    diagnosing_doctor_outputs = []
    questioning_doctor_outputs = []
    treatment_plans = []
    return process_vignette(idx, vignette_text, disease)


if __name__ == "__main__":
    os.makedirs("summarizer_outputs", exist_ok=True)
    os.makedirs("patient_followups", exist_ok=True)
    os.makedirs("diagnosing_doctor_outputs", exist_ok=True)
    os.makedirs("questioning_doctor_outputs", exist_ok=True)
    os.makedirs("treatment_plans", exist_ok=True)

    with open("dataset_generation/Again/disease_vignettes.json", "r") as f:
        vignette_dict = json.load(f)

    flattened_vignettes = []
    for disease, vignettes in vignette_dict.items():
        for vignette in vignettes[:2]:  # Only take the first 2
            flattened_vignettes.append((disease, vignette))

    # Launch multiprocessing pool with 10 workers
    with multiprocessing.Pool(processes=10) as pool:
        results = pool.map(
            run_vignette_task,
            [
                (idx, vignette_text, disease)
                for idx, (disease, vignette_text) in enumerate(flattened_vignettes)
            ],
        )

    # Aggregate and save all results to JSON
    all_patient_followups = []
    all_summarizer_outputs = []
    all_diagnosing_doctor_outputs = []
    all_questioning_doctor_outputs = []
    all_treatment_plans = []

    for result in results:
        all_patient_followups.extend(result["patient_response"])
        all_summarizer_outputs.extend(result["summarizer_outputs"])
        all_diagnosing_doctor_outputs.extend(result["diagnosing_doctor_outputs"])
        all_questioning_doctor_outputs.extend(result["questioning_doctor_outputs"])
        all_treatment_plans.extend(result["treatment_plans"])

    with open("patient_followups.json", "w") as f:
        json.dump(all_patient_followups, f, indent=2)
    with open("summarizer_outputs.json", "w") as f:
        json.dump(all_summarizer_outputs, f, indent=2)
    with open("diagnosing_doctor_outputs.json", "w") as f:
        json.dump(all_diagnosing_doctor_outputs, f, indent=2)
    with open("questioning_doctor_outputs.json", "w") as f:
        json.dump(all_questioning_doctor_outputs, f, indent=2)
    with open("treatment_plans.json", "w") as f:
        json.dump(all_treatment_plans, f, indent=2)

    print("\n✅ All role outputs saved.")

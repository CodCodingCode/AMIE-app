import os
import json
from openai import OpenAI
import time
import multiprocessing
import shutil

# Initialize OpenAI client
client = OpenAI(api_key="api")  # Replace with your actual API key
model = "gpt-4.1-nano"

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
Just say what you're feeling — physically or emotionally — in two to three sentences. 

YOU MUST mention your age, and biological gender in the first of the three sentences. E.g. "I am 25, and I am a biological male."

YOU MUST RESPOND IN THE FOLLOWING FORMAT:
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
            "output": raw_patient,
        }
    )
    turn_count = 0  # Doctor + patient
    diagnosis_complete = False
    prev_vignette_summary = ""

    while not diagnosis_complete:
        joined_conversation = "\\n".join(conversation)
        if turn_count > 6:
            vignette_summary = summarizer.ask(
                f"""You are a clinical summarizer trained to extract structured vignettes from doctor–patient dialogues.

    Use the gold diagnosis only to assess whether the patient's reported symptoms are consistent or missing anything important — DO NOT use it to hallucinate or invent new symptoms.

    Gold Diagnosis: {gold_label}
    Do not mention the gold-standard diagnosis in your response; use it only internally for reasoning. DO NOT MENTION IT IN THE THINKING PROCESS OR THE ANSWER. DO NOT EVEN MENTION THE GOLD LABEL IN ANY OF YOUR OUTPUT.

    Build a cumulative, ever-growing FULL VIGNETTE by restating all previously confirmed facts and appending any newly mentioned details. Only summarize confirmed facts explicitly stated by the patient or the doctor. Do not speculate.
    YOU MUST RESPOND IN THE FOLLOWING FORMAT:

    THINKING: <Your reasoning about whether the conversation introduced new clinical details>. 
    ANSWER: <Newly updated vignette>.

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
                    "input": joined_conversation,
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

    If you believe the dialogue should end, explicitly confirm each of the following in your THINKING (checklist style):
    - Does the vignette fully support the gold label?
    - Is there no meaningful diagnostic uncertainty remaining?
    - Has the conversation had at least 8 total turns (excluding summaries)?
    - Is any further clarification, lab, or follow-up unnecessary?

    If all of these are clearly true, you MUST output END after your diagnosis.

    Do not mention the gold-standard diagnosis in your response; use it only internally for reasoning. DO NOT MENTION IT IN THE THINKING PROCESS OR THE ANSWER. DO NOT EVEN MENTION THE GOLD LABEL IN ANY OF YOUR OUTPUT.

    YOU MUST RESPOND IN THE FOLLOWING FORMAT:

    THINKING: <Your reasoning about the diagnosis, including any differential diagnoses you considered and why you chose this one>.
    ANSWER: <Your most likely diagnosis and END if all statments are met>.

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
                    raw_treatment = diagnoser.ask(
                        f"""You are a board-certified clinician. Based on the diagnosis and patient vignette provided below, suggest a concise treatment plan that could realistically be initiated by a primary care physician or psychiatrist.

            Diagnosis: {diagnosis}
            Vignette: {vignette_summary}

            Include both non-pharmacological and pharmacological interventions if appropriate. Limit your plan to practical, real-world guidance. Please make sure to output your diagnosis plan in pargraph format, not in bullet points.

            Provide your reasoning and final plan in the following format:

            THINKING: <your reasoning about why you chose this treatment>
            ANSWER: <the actual treatment plan>
            """
                    )
                    print("💊 Raw Treatment Plan:", raw_treatment)

                    treatment_plans.append(
                        {
                            "vignette_index": idx,
                            "input": diagnosis,
                            "output": raw_treatment,
                        }
                    )

                    diagnosis_complete = True
                    break
                else:
                    print(
                        f"⚠️ Model said END before 10 turns. Ignoring END due to insufficient conversation length."
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
    Ask ONLY questions that may add new data to the current patient Vignette.

    Previously asked questions: {json.dumps(previous_questions)}

    Do not mention the gold-standard diagnosis in your response; use it only internally for reasoning. DO NOT MENTION IT IN THE THINKING PROCESS OR THE ANSWER. DO NOT EVEN MENTION THE GOLD LABEL IN ANY OF YOUR OUTPUT.

    YOU MUST RESPOND IN THE FOLLOWING FORMAT:

    THINKING: <Why this question adds diagnostic value>.
    ANSWER: <Your next question'>.

    Vignette:\n{vignette_summary}
    Current Estimated Diagnosis: {diagnosis}
    """
            )
            if "ANSWER:" in raw_followup:
                followup_question = raw_followup.split("ANSWER:")[1].strip()
            else:
                followup_question = raw_followup
            print("❓ Follow-up:", followup_question)
            question_input = f"Vignette:\n{vignette_summary}\nCurrent Estimated Diagnosis: {diagnosis}"
            questioning_doctor_outputs.append(
                {
                    "vignette_index": idx,
                    "input": question_input,
                    "output": raw_followup,
                }
            )
            conversation.append(f"DOCTOR: {followup_question}")

            # Step 5: Patient answers
            raw_patient_fb = patient.ask(
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

    YOU MUST RESPOND IN THE FOLLOWING FORMAT:
    THINKING: <your thinking as a model on how a patient should respond to the doctor.>
    ANSWER: <your vague, real-patient-style reply to the doctor>

    Patient background: {vignette_text}
    Doctor's question: {followup_question}"""
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

        else:
            vignette_summary = summarizer.ask(
                f"""You are a clinical summarizer trained to extract structured vignettes from doctor–patient dialogues.

    Build a cumulative, ever-growing FULL VIGNETTE by restating all previously confirmed facts and appending any newly mentioned details. Only summarize confirmed facts explicitly stated by the patient or the doctor. Do not speculate.
    YOU MUST RESPOND IN THE FOLLOWING FORMAT:
    
    THINKING: <Your reasoning about whether the conversation introduced new clinical details>. 
    ANSWER: <The Patient Vignette>.

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
                    "input": joined_conversation,
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

    Your job is to:
    - Think through alternative plausible diagnoses
    - Justify why some are more likely or less likely

    If you believe the dialogue should end, explicitly confirm each of the following in your THINKING (checklist style):
    - Is there no meaningful diagnostic uncertainty remaining?
    - Has the conversation had at least 8 total turns (excluding summaries)?
    - Is any further clarification, lab, or follow-up unnecessary?

    If all of these are clearly true, you MUST output END after your diagnosis.

    YOU MUST RESPOND IN THE FOLLOWING FORMAT:

    THINKING: <Your reasoning about the diagnosis, including any differential diagnoses you considered and why you chose this one>.
    ANSWER: <Your most likely diagnosis and END if all statments are met>.

    
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
                    raw_treatment = diagnoser.ask(
                        f"""You are a board-certified clinician. Based on the diagnosis provided below, suggest a concise treatment plan that could realistically be initiated by a primary care physician or psychiatrist.

            Diagnosis: {diagnosis}

            Include both non-pharmacological and pharmacological interventions if appropriate. Limit your plan to practical, real-world guidance. Please make sure to output your diagnosis plan in pargraph format, not in bullet points.

            Provide your reasoning and final plan in the following format:

            THINKING: <your reasoning about why you chose this treatment>
            ANSWER: <the actual treatment plan>
            """
                    )
                    print("💊 Raw Treatment Plan:", raw_treatment)

                    treatment_plans.append(
                        {
                            "vignette_index": idx,
                            "input": diagnosis,
                            "output": raw_treatment,
                        }
                    )

                    diagnosis_complete = True
                    break
                else:
                    print(
                        f"⚠️ Model said END before 10 turns. Ignoring END due to insufficient conversation length."
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

    Please ask questions that may add new data to the current patient Vignette.

    Previously asked questions: {json.dumps(previous_questions)}

    YOU MUST RESPOND IN THE FOLLOWING FORMAT:

    THINKING: <Why this question adds diagnostic value>.
    ANSWER: <Your next question'>.

    Vignette:\n{vignette_summary}
    Current Estimated Diagnosis: {diagnosis}
    """
            )
            if "ANSWER:" in raw_followup:
                followup_question = raw_followup.split("ANSWER:")[1].strip()
            else:
                followup_question = raw_followup
            print("❓ Follow-up:", followup_question)
            question_input = f"Vignette:\n{vignette_summary}\nCurrent Estimated Diagnosis: {diagnosis}"
            questioning_doctor_outputs.append(
                {
                    "vignette_index": idx,
                    "input": question_input,
                    "output": raw_followup,
                }
            )
            conversation.append(f"DOCTOR: {followup_question}")

            # Step 5: Patient answers
            raw_patient_fb = patient.ask(
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

    YOU MUST RESPOND IN THE FOLLOWING FORMAT:
    THINKING: <your thinking as a model on how a patient should respond to the doctor.>
    ANSWER: <your vague, real-patient-style reply to the doctor>

    Patient background: {vignette_text}
    Doctor's question: {followup_question}"""
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

    with open(f"2summarizer_outputs/summarizer_{idx}.json", "w") as f:
        json.dump(summarizer_outputs, f, indent=2)
    with open(f"2patient_followups/patient_{idx}.json", "w") as f:
        json.dump(patient_response, f, indent=2)
    with open(f"2diagnosing_doctor_outputs/diagnoser_{idx}.json", "w") as f:
        json.dump(diagnosing_doctor_outputs, f, indent=2)
    with open(f"2questioning_doctor_outputs/questioner_{idx}.json", "w") as f:
        json.dump(questioning_doctor_outputs, f, indent=2)
    with open(f"2treatment_plans/treatment_{idx}.json", "w") as f:
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
    # Remove and recreate output directories to start empty
    output_dirs = [
        "2summarizer_outputs",
        "2patient_followups",
        "2diagnosing_doctor_outputs",
        "2questioning_doctor_outputs",
        "2treatment_plans",
    ]
    for directory in output_dirs:
        if os.path.exists(directory):
            shutil.rmtree(directory)
        os.makedirs(directory, exist_ok=True)

    os.makedirs("2summarizer_outputs", exist_ok=True)
    os.makedirs("2patient_followups", exist_ok=True)
    os.makedirs("2diagnosing_doctor_outputs", exist_ok=True)
    os.makedirs("2questioning_doctor_outputs", exist_ok=True)
    os.makedirs("2treatment_plans", exist_ok=True)

    with open(
        "/Users/owner/Downloads/coding projects/AMIE-app/validated_disease_vignettes.json",
        "r",
    ) as f:
        vignette_dict = json.load(f)

    flattened_vignettes = []
    for disease, vignettes in vignette_dict.items():
        # Only process if we have a list of vignettes
        if not isinstance(vignettes, list):
            continue
        for vignette in vignettes[:2]:  # Only take the first 2
            flattened_vignettes.append((disease, vignette))

    # Launch multiprocessing pool with 10 workers
    with multiprocessing.Pool(processes=12) as pool:
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

    with open("2patient_followups.json", "w") as f:
        json.dump(all_patient_followups, f, indent=2)
    with open("2summarizer_outputs.json", "w") as f:
        json.dump(all_summarizer_outputs, f, indent=2)
    with open("2diagnosing_doctor_outputs.json", "w") as f:
        json.dump(all_diagnosing_doctor_outputs, f, indent=2)
    with open("2questioning_doctor_outputs.json", "w") as f:
        json.dump(all_questioning_doctor_outputs, f, indent=2)
    with open("2treatment_plans.json", "w") as f:
        json.dump(all_treatment_plans, f, indent=2)

    print("\n✅ All role outputs saved.")

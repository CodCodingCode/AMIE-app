# process_vignette.py
"""
Core vignette processing logic for the medical diagnosis simulation.
"""

import json
from role_responder import RoleResponder
from agents import (
    PatientInterpreter,
    BehaviorAnalyzer,
    ClinicalSummarizer,
    DiagnosticsExpert,
    ClinicalQuestioner,
)
from patient_behaviors import select_patient_behavior, generate_patient_prompt_modifiers
from prompts import (
    INITIAL_PATIENT_PROMPT,
    FOLLOWUP_PATIENT_PROMPT,
    TREATMENT_PLAN_PROMPT,
)


def process_vignette(idx, vignette_text, gold_label, client, model):
    """Process a single vignette through the diagnostic conversation"""
    
    # Initialize tracking lists
    conversation = []
    patient_response = []
    summarizer_outputs = []
    diagnosing_doctor_outputs = []
    questioning_doctor_outputs = []
    treatment_plans = []
    behavioral_analyses = []
    patient_interpretations = []
    
    # Initialize agents
    behavior_analyzer = BehaviorAnalyzer(client, model)
    patient_interpreter = PatientInterpreter(client, model)
    clinical_summarizer = ClinicalSummarizer(client, model)
    diagnostics_expert = DiagnosticsExpert(client, model)
    clinical_questioner = ClinicalQuestioner(client, model)

    # Select patient behavior for this vignette
    behavior_type, behavior_config = select_patient_behavior()
    print(f"🎭 Selected patient behavior: {behavior_type} - {behavior_config['description']}")
    print(f"🎯 Gold diagnosis: {gold_label}")

    previous_questions = []
    initial_prompt = "What brings you in today?"
    conversation.clear()
    conversation.append(f"DOCTOR: {initial_prompt}")

    # Create patient with behavior-specific instructions
    patient_instructions = generate_patient_prompt_modifiers(
        behavior_config, is_initial=True
    )
    patient = RoleResponder(patient_instructions, client, model)

    # Age and gender requirements with behavior consideration
    age_gender_instruction = 'YOU MUST mention your age, and biological gender in the first of the three sentences. E.g. "I am 25, and I am a biological male."'

    # Adjust response length based on behavior
    response_length = "in two to three sentences"
    if "excessive_details" in behavior_config.get("modifiers", []):
        response_length = "in three to four sentences, including relevant background details"
    elif "symptom_minimization" in behavior_config.get("modifiers", []):
        response_length = "in one to two brief sentences"

    prompt = INITIAL_PATIENT_PROMPT.format(
        patient_instructions=patient_instructions,
        response_length=response_length,
        age_gender_instruction=age_gender_instruction,
        vignette_text=vignette_text,
        initial_prompt=initial_prompt
    )

    turn_count = 0
    diagnosis_complete = False
    prev_vignette_summary = ""

    patient_result = patient.ask(prompt)
    raw_patient = patient_result["raw"]
    patient_response_text = patient_result["clean"]

    print("🗣️ Patient's Reply:", patient_response_text)
    conversation.append(f"PATIENT: {patient_response_text}")
    patient_response.append(
        {
            "vignette_index": idx,
            "input": f"{vignette_text}\n{initial_prompt}",
            "output": raw_patient,
            "behavior_type": behavior_type,
            "behavior_config": behavior_config,
            "gold_diagnosis": gold_label,
        }
    )

    while not diagnosis_complete:
        # Detect patient behavior patterns
        behavioral_result = behavior_analyzer.detect_patient_behavior_cues(
            conversation, patient_response
        )
        behavioral_analysis_raw = behavioral_result["raw"]
        behavioral_analysis = behavioral_result["clean"]

        behavioral_analyses.append(
            {
                "vignette_index": idx,
                "turn_count": turn_count,
                "analysis": behavioral_analysis_raw,
            }
        )

        # Interpret patient communication
        interpretation_result = patient_interpreter.interpret_patient_communication(
            conversation, behavioral_analysis, prev_vignette_summary
        )
        patient_interpretation_raw = interpretation_result["raw"]
        patient_interpretation = interpretation_result["clean"]

        patient_interpretations.append(
            {
                "vignette_index": idx,
                "turn_count": turn_count,
                "interpretation": patient_interpretation_raw,
            }
        )
        print(f"🔍 Patient Interpretation: {patient_interpretation[:100]}...")

        # Generate unbiased vignette
        vignette_result = clinical_summarizer.generate_unbiased_vignette(
            conversation, prev_vignette_summary, patient_interpretation
        )
        vignette_summary_raw = vignette_result["raw"]
        vignette_summary = vignette_result["clean"]

        # Check for corrupted state
        if "Unable to extract answer content properly" in vignette_summary:
            print(f"❌ CORRUPTED VIGNETTE DETECTED!")
            print(f"Setting fallback vignette...")
            vignette_summary = f"Patient presents with symptoms. Turn count: {turn_count}"

        summarizer_outputs.append(
            {
                "vignette_index": idx,
                "input": f"CONVERSATION HISTORY:\n{json.dumps(conversation, indent=2)}\n\nPREVIOUS VIGNETTE:\n{prev_vignette_summary}\n\nPATIENT COMMUNICATION ANALYSIS:\n{patient_interpretation}",
                "output": vignette_summary_raw,
                "turn_count": turn_count,
                "gold_diagnosis": gold_label,
            }
        )

        prev_vignette_summary = vignette_summary

        # Get diagnosis
        print("Turn count:", turn_count)
        diagnosis_result, stage, disease_data = diagnostics_expert.get_diagnosis_response(
            turn_count, gold_label, vignette_summary, previous_questions
        )
        diagnosis_raw = diagnosis_result["raw"]
        diagnosis = diagnosis_result["clean"]

        # Determine letter for stage
        letter = "E" if turn_count < 4 else "M" if turn_count < 8 else "L"

        diagnosing_doctor_outputs.append(
            {
                "vignette_index": idx,
                "input": vignette_summary,
                "output": diagnosis_raw,
                "turn_count": turn_count,
                "letter": letter,
                "gold_diagnosis": gold_label,
            }
        )

        # Handle END signal
        if "END" in diagnosis:
            if turn_count >= 8:
                diagnosis_complete = True
                print(f"✅ Reached END for vignette {idx}. Moving to treatment planning.\n")
                
                # Generate treatment plan
                treatment_prompt = TREATMENT_PLAN_PROMPT.format(
                    diagnosis=diagnosis,
                    gold_label=gold_label,
                    vignette_summary=vignette_summary,
                    behavior_type=behavior_type
                )

                treatment_result = diagnostics_expert.responder.ask(treatment_prompt)
                raw_treatment = treatment_result["raw"]

                treatment_plans.append(
                    {
                        "vignette_index": idx,
                        "input": diagnosis,
                        "output": raw_treatment,
                        "gold_diagnosis": gold_label,
                    }
                )

        # Generate next question if not complete
        if not diagnosis_complete:
            # Limit to last 3–5 doctor questions
            previous_questions = [
                entry.replace("DOCTOR:", "").strip()
                for entry in conversation
                if entry.startswith("DOCTOR:")
            ][-5:]

            # Generate follow-up question
            followup_result = clinical_questioner.generate_question(
                turn_count, previous_questions, vignette_summary,
                diagnosis, behavioral_analysis, gold_label, disease_data
            )
            raw_followup = followup_result["raw"]
            followup_question = followup_result["clean"]

            print("❓ Empathetic Follow-up:", followup_question)
            questioning_doctor_outputs.append(
                {
                    "vignette_index": idx,
                    "input": vignette_summary + diagnosis + behavioral_analysis,
                    "output": raw_followup,
                    "letter": letter,
                    "behavioral_cues": behavioral_analysis,
                    "gold_diagnosis": gold_label,
                }
            )
            conversation.append(f"DOCTOR: {followup_question}")

            # Update patient instructions for follow-up
            patient_followup_instructions = generate_patient_prompt_modifiers(
                behavior_config, is_initial=False
            )
            patient = RoleResponder(patient_followup_instructions, client, model)

            # Adjust response style based on behavior and conversation stage
            response_guidance = "in one or two sentences"
            if "excessive_details" in behavior_config.get("modifiers", []):
                response_guidance = "in two to three sentences with additional context"
            elif turn_count >= 10 and "gradual_revelation" in behavior_config.get("modifiers", []):
                response_guidance = "in one to three sentences, being more open than initially"

            # Get patient response
            prompt = FOLLOWUP_PATIENT_PROMPT.format(
                patient_followup_instructions=patient_followup_instructions,
                behavior_type=behavior_type,
                vignette_text=vignette_text,
                followup_question=followup_question,
                response_guidance=response_guidance
            )

            patient_fb_result = patient.ask(prompt)
            raw_patient_fb = patient_fb_result["raw"]
            patient_followup_text = patient_fb_result["clean"]

            print("🗣️ Patient:", patient_followup_text)
            conversation.append(f"PATIENT: {patient_followup_text}")
            patient_response.append(
                {
                    "vignette_index": idx,
                    "input": vignette_text + followup_question + behavior_type,
                    "output": raw_patient_fb,
                    "behavior_type": behavior_type,
                    "turn_count": turn_count,
                    "gold_diagnosis": gold_label,
                }
            )

            turn_count += 2

    # Save behavior metadata
    behavior_metadata = {
        "behavior_type": behavior_type,
        "behavior_description": behavior_config["description"],
        "modifiers": behavior_config.get("modifiers", []),
        "empathy_cues": behavior_config.get("empathy_cues", []),
        "gold_diagnosis": gold_label,
    }

    # Save individual outputs
    outputs = {
        "summarizer_outputs": summarizer_outputs,
        "patient_followups": patient_response,
        "diagnosing_doctor_outputs": diagnosing_doctor_outputs,
        "questioning_doctor_outputs": questioning_doctor_outputs,
        "treatment_plans": treatment_plans,
        "behavior_metadata": [behavior_metadata],
        "behavioral_analyses": behavioral_analyses,
    }

    for output_type, data in outputs.items():
        filename = f"2{output_type}/{output_type.split('_')[0]}_{idx}.json"
        with open(filename, "w") as f:
            json.dump(data, f, indent=2)

    return {
        "vignette_index": idx,
        "patient_response": patient_response,
        "summarizer_outputs": summarizer_outputs,
        "diagnosing_doctor_outputs": diagnosing_doctor_outputs,
        "questioning_doctor_outputs": questioning_doctor_outputs,
        "treatment_plans": treatment_plans,
        "behavior_metadata": behavior_metadata,
        "behavioral_analyses": behavioral_analyses,
        "gold_diagnosis": gold_label,
    }
import os
import json
from openai import OpenAI
import time
import multiprocessing
import shutil
from itertools import islice
import random

# Initialize OpenAI client
client = OpenAI(api_key="api")  # Replace with your actual API key
model = "gpt-4.1-nano"

treatment_plans = []

# === Patient Behavior Configurations ===
PATIENT_BEHAVIORS = {
    "baseline": {
        "weight": 0.4,
        "description": "Standard patient behavior",
        "modifiers": [],
        "empathy_cues": []
    },
    "information_withholder": {
        "weight": 0.15,
        "description": "Patient initially omits embarrassing or stigmatized symptoms",
        "modifiers": ["embarrassed_symptoms", "gradual_revelation"],
        "empathy_cues": ["hesitation", "vague_responses", "embarrassment", "trust_building_needed"]
    },
    "anxious_amplifier": {
        "weight": 0.12,
        "description": "Patient with health anxiety who amplifies symptoms",
        "modifiers": ["catastrophic_thinking", "symptom_amplification", "multiple_concerns"],
        "empathy_cues": ["high_anxiety", "catastrophic_language", "reassurance_seeking", "fear_expression"]
    },
    "stoic_minimizer": {
        "weight": 0.12,
        "description": "Patient who downplays symptoms and delays care",
        "modifiers": ["symptom_minimization", "delayed_care_seeking", "tough_attitude"],
        "empathy_cues": ["downplaying", "reluctance", "pride_in_toughness", "external_pressure"]
    },
    "chronology_confused": {
        "weight": 0.1,
        "description": "Patient confused about symptom timing and progression",
        "modifiers": ["timeline_confusion", "sequence_uncertainty"],
        "empathy_cues": ["confusion", "uncertainty", "memory_issues", "needs_patience"]
    },
    "tangential_storyteller": {
        "weight": 0.08,
        "description": "Patient who includes irrelevant details and stories",
        "modifiers": ["excessive_details", "family_stories", "tangential_information"],
        "empathy_cues": ["storytelling", "context_sharing", "social_needs", "relationship_focus"]
    },
    "worried_family_involved": {
        "weight": 0.03,
        "description": "Family member influences patient responses",
        "modifiers": ["family_influence", "secondary_concerns"],
        "empathy_cues": ["family_pressure", "caregiver_stress", "divided_attention", "responsibility_burden"]
    }
}


# === Gold Diagnosis Integration Functions ===
def generate_gold_guided_prompt(base_prompt, gold_diagnosis, stage, vignette_summary):
    """
    Generate diagnostic prompts that subtly guide toward correct diagnosis without revealing it
    """
    # Create contextual hints based on gold diagnosis
    diagnostic_hints = create_diagnostic_hints(gold_diagnosis, stage)

    guided_prompt = f"""
    {base_prompt}
    
    DIAGNOSTIC GUIDANCE (Internal reasoning only - do not mention these directly):
    {diagnostic_hints}
    
    Focus your differential on conditions that match the clinical presentation patterns described above.
    Consider both common presentations and atypical variants of the suggested condition categories.
    """

    return guided_prompt


def create_diagnostic_hints(gold_diagnosis, stage):
    """
    Create subtle hints that guide toward correct diagnosis without revealing it
    """
    # Database of diagnostic categories and patterns
    diagnostic_patterns = {
        # Cardiovascular
        "myocardial infarction": {
            "patterns": [
                "acute chest pain syndromes",
                "coronary artery disease complications",
                "cardiac enzyme elevation patterns",
            ],
            "key_features": [
                "chest pain character",
                "radiation patterns",
                "associated autonomic symptoms",
            ],
            "red_flags": [
                "acute coronary syndrome presentations",
                "hemodynamic instability signs",
            ],
        },
        "hypertension": {
            "patterns": [
                "elevated blood pressure syndromes",
                "cardiovascular risk factors",
                "end-organ damage signs",
            ],
            "key_features": [
                "blood pressure readings",
                "headache patterns",
                "visual changes",
            ],
            "red_flags": ["hypertensive emergency signs", "target organ damage"],
        },
        "heart failure": {
            "patterns": [
                "fluid retention syndromes",
                "decreased exercise tolerance",
                "cardiac pump dysfunction",
            ],
            "key_features": [
                "dyspnea patterns",
                "fluid retention signs",
                "functional capacity",
            ],
            "red_flags": ["acute decompensation signs", "cardiogenic shock indicators"],
        },
        # Respiratory
        "asthma": {
            "patterns": [
                "reversible airway obstruction",
                "allergic respiratory syndromes",
                "bronchospasm presentations",
            ],
            "key_features": [
                "wheezing patterns",
                "trigger identification",
                "response to bronchodilators",
            ],
            "red_flags": [
                "severe bronchospasm signs",
                "respiratory failure indicators",
            ],
        },
        "pneumonia": {
            "patterns": [
                "infectious respiratory syndromes",
                "consolidative lung processes",
                "systemic infection signs",
            ],
            "key_features": [
                "cough characteristics",
                "fever patterns",
                "respiratory symptoms",
            ],
            "red_flags": ["sepsis indicators", "respiratory failure signs"],
        },
        "copd": {
            "patterns": [
                "chronic obstructive lung disease",
                "smoking-related respiratory conditions",
                "progressive dyspnea syndromes",
            ],
            "key_features": [
                "smoking history",
                "exertional dyspnea",
                "chronic cough patterns",
            ],
            "red_flags": ["acute exacerbation signs", "respiratory failure indicators"],
        },
        # Gastrointestinal
        "gastroesophageal reflux disease": {
            "patterns": [
                "acid-related disorders",
                "esophageal irritation syndromes",
                "upper GI symptoms",
            ],
            "key_features": [
                "heartburn patterns",
                "meal relationship",
                "positional factors",
            ],
            "red_flags": ["esophageal complications", "alarm symptoms"],
        },
        "appendicitis": {
            "patterns": [
                "acute abdominal pain syndromes",
                "right lower quadrant pathology",
                "surgical abdomen presentations",
            ],
            "key_features": [
                "pain migration patterns",
                "peritoneal signs",
                "systemic inflammation",
            ],
            "red_flags": ["peritonitis signs", "perforation indicators"],
        },
        # Endocrine
        "diabetes mellitus": {
            "patterns": [
                "hyperglycemic syndromes",
                "metabolic disorders",
                "polyuria-polydipsia presentations",
            ],
            "key_features": [
                "glucose metabolism",
                "osmotic symptoms",
                "metabolic complications",
            ],
            "red_flags": ["diabetic emergency signs", "ketoacidosis indicators"],
        },
        "hypothyroidism": {
            "patterns": [
                "thyroid hormone deficiency",
                "metabolic slowdown syndromes",
                "fatigue-related conditions",
            ],
            "key_features": [
                "energy levels",
                "temperature regulation",
                "cognitive function",
            ],
            "red_flags": ["myxedema signs", "severe hypothyroid complications"],
        },
        # Neurological
        "stroke": {
            "patterns": [
                "acute neurological deficits",
                "cerebrovascular syndromes",
                "focal brain dysfunction",
            ],
            "key_features": [
                "neurological deficit patterns",
                "onset characteristics",
                "vascular risk factors",
            ],
            "red_flags": ["large vessel occlusion signs", "hemorrhagic transformation"],
        },
        "migraine": {
            "patterns": [
                "primary headache disorders",
                "neurovascular headache syndromes",
                "episodic neurological symptoms",
            ],
            "key_features": [
                "headache characteristics",
                "associated symptoms",
                "trigger patterns",
            ],
            "red_flags": ["secondary headache signs", "neurological complications"],
        },
        # Musculoskeletal
        "osteoarthritis": {
            "patterns": [
                "degenerative joint disease",
                "mechanical joint pain",
                "age-related joint changes",
            ],
            "key_features": [
                "joint pain patterns",
                "functional limitations",
                "morning stiffness",
            ],
            "red_flags": [
                "inflammatory arthritis signs",
                "joint destruction indicators",
            ],
        },
        "rheumatoid arthritis": {
            "patterns": [
                "inflammatory arthritis",
                "autoimmune joint disease",
                "systemic inflammatory conditions",
            ],
            "key_features": [
                "joint inflammation patterns",
                "morning stiffness",
                "symmetrical involvement",
            ],
            "red_flags": ["extra-articular manifestations", "joint destruction signs"],
        },
        # Mental Health
        "depression": {
            "patterns": [
                "mood disorders",
                "anhedonia syndromes",
                "neurovegetative symptom complexes",
            ],
            "key_features": ["mood changes", "interest levels", "sleep patterns"],
            "red_flags": ["suicidal ideation", "psychotic features"],
        },
        "anxiety disorders": {
            "patterns": [
                "anxiety spectrum disorders",
                "autonomic hyperarousal",
                "worry-related conditions",
            ],
            "key_features": [
                "anxiety symptoms",
                "avoidance behaviors",
                "physical manifestations",
            ],
            "red_flags": ["panic attack features", "severe functional impairment"],
        },
        # Commonly Misdiagnosed
        "fibromyalgia": {
            "patterns": [
                "chronic pain syndromes",
                "central sensitization conditions",
                "widespread pain disorders",
            ],
            "key_features": ["pain distribution", "tender points", "sleep disturbance"],
            "red_flags": ["inflammatory conditions", "systemic disease signs"],
        },
        "systemic lupus erythematosus": {
            "patterns": [
                "autoimmune connective tissue disease",
                "multi-system inflammatory conditions",
                "antinuclear antibody syndromes",
            ],
            "key_features": [
                "systemic symptoms",
                "skin manifestations",
                "joint involvement",
            ],
            "red_flags": ["organ involvement", "severe systemic manifestations"],
        },
        "celiac disease": {
            "patterns": [
                "malabsorption syndromes",
                "gluten-related disorders",
                "autoimmune enteropathy",
            ],
            "key_features": [
                "gastrointestinal symptoms",
                "malabsorption signs",
                "dietary relationships",
            ],
            "red_flags": ["nutritional deficiencies", "severe malabsorption"],
        },
    }

    # Get pattern for gold diagnosis (case-insensitive matching)
    gold_lower = gold_diagnosis.lower()
    pattern_info = None

    for condition, info in diagnostic_patterns.items():
        if condition in gold_lower or any(
            word in gold_lower for word in condition.split()
        ):
            pattern_info = info
            break

    # If no specific pattern found, create generic guidance
    if not pattern_info:
        return f"""
        Consider conditions that present with the clinical features described in the vignette.
        Focus on both common and uncommon presentations of conditions that match this symptom complex.
        Pay attention to the temporal pattern and associated symptoms.
        """

    # Stage-specific guidance
    if stage == "early":  # 10 diagnoses
        return f"""
        Consider these diagnostic categories: {', '.join(pattern_info['patterns'])}.
        Key clinical features to evaluate: {', '.join(pattern_info['key_features'])}.
        Include both common and less common conditions that could present this way.
        """
    elif stage == "middle":  # 5 diagnoses
        return f"""
        Focus on: {', '.join(pattern_info['patterns'][:2])}.
        Critical features to assess: {', '.join(pattern_info['key_features'][:2])}.
        Narrow to conditions most consistent with the clinical presentation.
        """
    else:  # Late stage - 1-3 diagnoses
        return f"""
        Primary consideration: {pattern_info['patterns'][0]}.
        Key confirmatory features: {pattern_info['key_features'][0]}.
        Warning signs to evaluate: {', '.join(pattern_info['red_flags'])}.
        """


def generate_guided_questioner_prompt(base_prompt, gold_diagnosis, current_vignette):
    """
    Generate questioning prompts that guide toward information relevant to gold diagnosis
    """
    # Get relevant questions for the gold diagnosis
    relevant_questions = get_relevant_questions(gold_diagnosis, current_vignette)

    guided_prompt = f"""
    {base_prompt}
    
    CLINICAL FOCUS AREAS (Guide question selection without mentioning specific conditions):
    {relevant_questions}
    
    Ask questions that explore these areas while maintaining natural conversation flow.
    Do not directly mention any specific diagnoses.
    """

    return guided_prompt


def get_relevant_questions(gold_diagnosis, current_vignette):
    """
    Suggest relevant question areas based on gold diagnosis without revealing it
    """
    question_guidance = {
        "myocardial infarction": [
            "chest pain characteristics and radiation",
            "associated autonomic symptoms",
            "cardiac risk factors",
            "activity relationship",
        ],
        "asthma": [
            "breathing pattern details",
            "trigger identification",
            "exercise tolerance",
            "medication response history",
        ],
        "depression": [
            "mood and energy patterns",
            "sleep and appetite changes",
            "functional impact assessment",
            "interest and motivation levels",
        ],
        "diabetes mellitus": [
            "polyuria and polydipsia symptoms",
            "weight changes",
            "family history assessment",
            "energy and fatigue patterns",
        ],
        "fibromyalgia": [
            "pain distribution and quality",
            "sleep disturbance patterns",
            "fatigue characteristics",
            "functional impact assessment",
        ],
        "systemic lupus erythematosus": [
            "systemic symptoms assessment",
            "skin and joint manifestations",
            "constitutional symptoms",
            "organ system involvement",
        ],
    }

    # Get question areas for gold diagnosis
    gold_lower = gold_diagnosis.lower()
    for condition, questions in question_guidance.items():
        if condition in gold_lower:
            return f"Focus questioning on: {', '.join(questions)}"

    # Generic guidance if specific condition not found
    return "Focus on symptom characterization, temporal patterns, associated features, and functional impact"


def evaluate_diagnostic_accuracy(predicted_diagnoses, gold_diagnosis):
    """
    Evaluate how well the predicted diagnoses match the gold standard
    """
    # Extract diagnosis names from the model output
    predicted_list = extract_diagnosis_names(predicted_diagnoses)

    # Check if gold diagnosis is in the list (fuzzy matching)
    gold_found = False
    position = -1

    for i, pred in enumerate(predicted_list):
        if is_diagnosis_match(pred, gold_diagnosis):
            gold_found = True
            position = i + 1
            break

    return {
        "gold_diagnosis_found": gold_found,
        "position_in_list": position,
        "predicted_diagnoses": predicted_list,
        "accuracy_score": calculate_accuracy_score(
            gold_found, position, len(predicted_list)
        ),
    }


def extract_diagnosis_names(diagnosis_text):
    """Extract diagnosis names from model output"""
    import re

    # Look for numbered list pattern
    pattern = r"\d+\.\s*(?:Diagnosis:)?\s*([^\n]+?)(?:\s*Justification|$)"
    matches = re.findall(pattern, diagnosis_text, re.IGNORECASE | re.MULTILINE)

    # Clean up the extracted names
    cleaned = []
    for match in matches:
        # Remove common prefixes and clean up
        clean_name = re.sub(
            r"^(Diagnosis:?|Condition:?)\s*", "", match, flags=re.IGNORECASE
        )
        clean_name = clean_name.strip()
        if clean_name:
            cleaned.append(clean_name)

    return cleaned


def is_diagnosis_match(predicted, gold):
    """Check if predicted diagnosis matches gold diagnosis (fuzzy matching)"""
    pred_lower = predicted.lower()
    gold_lower = gold.lower()

    # Direct match
    if pred_lower == gold_lower:
        return True

    # Check if gold diagnosis words are in predicted
    gold_words = set(gold_lower.split())
    pred_words = set(pred_lower.split())

    # If most significant words match
    if len(gold_words & pred_words) >= min(2, len(gold_words) * 0.7):
        return True

    return False


def calculate_accuracy_score(found, position, total_predictions):
    """Calculate accuracy score based on whether gold diagnosis was found and its position"""
    if not found:
        return 0.0

    # Higher score for earlier positions
    if position == 1:
        return 1.0
    elif position <= 3:
        return 0.8
    elif position <= 5:
        return 0.6
    else:
        return 0.4


# === Modified process_vignette function ===
def process_vignette(idx, vignette_text, gold_label):
    global conversation, patient_response, summarizer_outputs, diagnosing_doctor_outputs, questioning_doctor_outputs, treatment_plans, behavioral_analyses

    # Select patient behavior for this vignette
    behavior_type, behavior_config = select_patient_behavior()
    print(
        f"🎭 Selected patient behavior: {behavior_type} - {behavior_config['description']}"
    )
    print(f"🎯 Gold diagnosis: {gold_label}")

    previous_questions = []
    initial_prompt = "What brings you in today?"
    conversation.clear()
    conversation.append(f"DOCTOR: {initial_prompt}")

    # Create patient with behavior-specific instructions
    patient_instructions = generate_patient_prompt_modifiers(
        behavior_config, is_initial=True
    )
    patient = RoleResponder(patient_instructions)

    # Age and gender requirements with behavior consideration
    age_gender_instruction = 'YOU MUST mention your age, and biological gender in the first of the three sentences. E.g. "I am 25, and I am a biological male."'

    # Adjust response length based on behavior
    response_length = "in two to three sentences"
    if "excessive_details" in behavior_config.get("modifiers", []):
        response_length = (
            "in three to four sentences, including relevant background details"
        )
    elif "symptom_minimization" in behavior_config.get("modifiers", []):
        response_length = "in one to two brief sentences"

    raw_patient = patient.ask(
        f"""{patient_instructions}

NEVER hallucinate past medical evaluations, tests, or diagnoses. 
Do NOT give clear medical names unless the doctor already told you. 
Don't jump to conclusions about your condition. 
Be vague, partial, emotional, even contradictory if needed. 
Just say what you're feeling — physically or emotionally — {response_length}. 

{age_gender_instruction}

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
            "behavior_type": behavior_type,
            "behavior_config": behavior_config,
            "gold_diagnosis": gold_label,
        }
    )
    turn_count = 0
    diagnosis_complete = False
    prev_vignette_summary = ""

    while not diagnosis_complete:
        joined_conversation = "\\n".join(conversation)
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

        # Detect behavioral cues for empathetic response
        if turn_count > 0:
            behavioral_analysis = detect_patient_behavior_cues(
                conversation, patient_response
            )
            behavioral_analyses.append(
                {
                    "vignette_index": idx,
                    "turn_count": turn_count,
                    "analysis": behavioral_analysis,
                }
            )
            print(f"🧠 Behavioral Analysis: {behavioral_analysis}")
        else:
            behavioral_analysis = f"Expected behavioral cues: {', '.join(behavior_config.get('empathy_cues', []))}"

        # === MODIFIED DIAGNOSIS LOGIC WITH GOLD GUIDANCE ===
        diagnosis = ""
        base_diagnosis_prompt = ""

        if turn_count < 6:
            base_diagnosis_prompt = """You are a board-certified diagnostician.

                    Your task is to:
                    - Generate a list of 10 plausible diagnoses based on the patient's presentation.
                    - For each diagnosis, provide a brief justification for its consideration.

                    Previously asked questions: {prev_questions}

                    Vignette:
                    {vignette}
                    Turn count: {turn_count}

                    Please respond in the following format:

                    THINKING:
                    - Consider the vignettes details
                    - Identify key symptoms, demographics, and clinical context

                    ANSWER:
                    1. Diagnosis: <Diagnosis Name>
                    Justification: <Reasoning for inclusion>
                    2. Diagnosis: <Diagnosis Name>
                    Justification: <Reasoning for inclusion>
                    ...
                    10. Diagnosis: <Diagnosis Name>
                        Justification: <Reasoning for inclusion>
                    """

            # Add gold diagnosis guidance
            guided_prompt = generate_gold_guided_prompt(
                base_diagnosis_prompt, gold_label, "early", vignette_summary
            )

            diagnosis = diagnoser.ask(
                guided_prompt.format(
                    prev_questions=json.dumps(previous_questions),
                    vignette=vignette_summary,
                    turn_count=turn_count,
                )
            )

        elif turn_count > 5 and turn_count < 11:
            base_diagnosis_prompt = """You are a board-certified diagnostician.

                    Your task is to:
                    - Refine the differential diagnosis list to the 5 most probable conditions.
                    - Provide a detailed justification for each, considering the patient's data and previous discussions.

                    Previously asked questions: {prev_questions}

                    Vignette:
                    {vignette}
                    Turn count: {turn_count}

                    Please respond in the following format:

                    THINKING:
                    - Consider the vignettes details
                    - Identify key symptoms, demographics, and clinical context
                    
                    ANSWER:
                    1. Diagnosis: <Diagnosis Name>
                    Justification: <Reasoning for inclusion>
                    2. Diagnosis: <Diagnosis Name>
                    Justification: <Reasoning for inclusion>
                    ...
                    5. Diagnosis: <Diagnosis Name>
                        Justification: <Reasoning for inclusion>
                    """

            guided_prompt = generate_gold_guided_prompt(
                base_diagnosis_prompt, gold_label, "middle", vignette_summary
            )

            diagnosis = diagnoser.ask(
                guided_prompt.format(
                    prev_questions=json.dumps(previous_questions),
                    vignette=vignette_summary,
                    turn_count=turn_count,
                )
            )

        elif turn_count >= 11:
            base_diagnosis_prompt = """You are a board-certified diagnostician.

                    Your task is to:
                    - Identify the most probable diagnosis.
                    - Justify why this diagnosis is the most likely.
                    - Determine if the diagnostic process should conclude based on the following checklist:
                    - Is there no meaningful diagnostic uncertainty remaining?
                    - Has the conversation had at least 8 total turns (excluding summaries)?
                    - Is any further clarification, lab, or follow-up unnecessary?

                    Previously asked questions: {prev_questions}

                    Vignette:
                    {vignette}

                    Please respond in the following format:

                    THINKING:
                    Diagnosis: <Diagnosis Name>
                    Justification: <Comprehensive reasoning>
                    - Consider the vignettes details
                    - Identify key symptoms, demographics, and clinical context
                    
                    Checklist:
                    - No diagnostic uncertainty remaining: <Yes/No>
                    - No further clarification needed: <Yes/No>

                    ANSWER:
                    <Diagnosis Name>
                    <If all checklist items are 'Yes', append 'END' to signify conclusion>
                    """

            guided_prompt = generate_gold_guided_prompt(
                base_diagnosis_prompt, gold_label, "late", vignette_summary
            )

            diagnosis = diagnoser.ask(
                guided_prompt.format(
                    prev_questions=json.dumps(previous_questions),
                    vignette=vignette_summary,
                )
            )

        # Evaluate diagnostic accuracy
        accuracy_eval = evaluate_diagnostic_accuracy(diagnosis, gold_label)
        print(f"🎯 Diagnostic Accuracy: {accuracy_eval}")

        print("Turn count:", turn_count)
        letter = ""
        stage = "early"
        if turn_count < 6:
            letter = "E"
            stage = "early"
        elif turn_count >= 5 and turn_count < 11:
            letter = "M"
            stage = "middle"
        elif turn_count >= 11:
            letter = "L"
            stage = "late"

        print("🔍 Diagnosis:", diagnosis)
        diagnosing_doctor_outputs.append(
            {
                "vignette_index": idx,
                "input": vignette_summary,
                "output": diagnosis,
                "turn_count": turn_count,
                "letter": letter,
                "gold_diagnosis": gold_label,
                "accuracy_evaluation": accuracy_eval,
            }
        )

        # Handle END signal explicitly
        if "END" in diagnosis:
            if turn_count >= 15:
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
                        "gold_diagnosis": gold_label,
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

        # === MODIFIED QUESTIONING WITH GOLD GUIDANCE ===
        base_questioning_role = ""
        if turn_count < 6:
            base_questioning_role = """Please ask an open-ended question that encourages the patient to share more about their symptoms and concerns, aiming to gather comprehensive information and establish rapport."""
        elif turn_count >= 5 and turn_count < 11:
            base_questioning_role = """Please ask questions that may add new data to the current patient Vignette while being sensitive to the patient's communication style."""
        else:
            base_questioning_role = """Please ask a focused question that helps confirm the most probable diagnosis and facilitates discussion of the management plan, ensuring the patient understands and agrees with the proposed approach."""

        # Add gold diagnosis guidance to questioning
        guided_questioning_role = generate_guided_questioner_prompt(
            base_questioning_role, gold_label, vignette_summary
        )

        # Create empathy-enhanced questioner
        empathetic_prompt = generate_empathetic_questioning_prompt(
            guided_questioning_role, behavioral_analysis, stage
        )
        questioner = RoleResponder(empathetic_prompt)

        raw_followup = questioner.ask(
            f"""Previously asked questions: {json.dumps(previous_questions)}

            YOU MUST RESPOND IN THE FOLLOWING FORMAT:

            THINKING: <Why this question adds diagnostic value AND how you're being empathetic to the patient's needs>.
            EMPATHY: <How you're acknowledging the patient's emotional state or communication style>
            ANSWER: <Your empathetic, diagnostically valuable question>.

            Vignette:
            {vignette_summary}
            Current Estimated Diagnosis: {diagnosis}
            Patient Behavioral Cues: {behavioral_analysis}
            """
        )

        if "ANSWER:" in raw_followup:
            followup_question = raw_followup.split("ANSWER:")[1].strip()
        else:
            followup_question = raw_followup
        print("❓ Empathetic Follow-up:", followup_question)
        question_input = f"Vignette:\n{vignette_summary}\nCurrent Estimated Diagnosis: {diagnosis}\nBehavioral Cues: {behavioral_analysis}"
        questioning_doctor_outputs.append(
            {
                "vignette_index": idx,
                "input": question_input,
                "output": raw_followup,
                "letter": letter,
                "behavioral_cues": behavioral_analysis,
                "gold_diagnosis": gold_label,
            }
        )
        conversation.append(f"DOCTOR: {followup_question}")

        # Update patient instructions for follow-up responses (behavior may evolve)
        patient_followup_instructions = generate_patient_prompt_modifiers(
            behavior_config, is_initial=False
        )
        patient = RoleResponder(patient_followup_instructions)

        # Adjust response style based on behavior and conversation stage
        response_guidance = "in one or two sentences"
        if "excessive_details" in behavior_config.get("modifiers", []):
            response_guidance = "in two to three sentences with additional context"
        elif turn_count >= 10 and "gradual_revelation" in behavior_config.get(
            "modifiers", []
        ):
            response_guidance = (
                "in one to three sentences, being more open than initially"
            )

        # Step 5: Patient answers
        raw_patient_fb = patient.ask(
            f"""{patient_followup_instructions}

NEVER hallucinate past medical evaluations, tests, or diagnoses. 
Do NOT give clear medical names unless the doctor already told you. 
Don't jump to conclusions about your condition. 
Be vague, partial, emotional, even contradictory if needed. 
Just say what you're feeling — physically or emotionally — {response_guidance}.

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
                "output": raw_patient_fb,
                "behavior_type": behavior_type,
                "turn_count": turn_count,
                "gold_diagnosis": gold_label,
            }
        )

        turn_count += 2

    # Save behavior metadata with the results
    behavior_metadata = {
        "behavior_type": behavior_type,
        "behavior_description": behavior_config["description"],
        "modifiers": behavior_config.get("modifiers", []),
        "empathy_cues": behavior_config.get("empathy_cues", []),
        "gold_diagnosis": gold_label,
    }

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
    with open(f"2behavior_metadata/behavior_{idx}.json", "w") as f:
        json.dump(behavior_metadata, f, indent=2)
    with open(f"2behavioral_analyses/behavioral_analysis_{idx}.json", "w") as f:
        json.dump(behavioral_analyses, f, indent=2)

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


# === Missing imports and classes ===
def select_patient_behavior():
    """Select patient behavior based on weighted probabilities"""
    rand = random.random()
    cumulative = 0
    for behavior, config in PATIENT_BEHAVIORS.items():
        cumulative += config["weight"]
        if rand <= cumulative:
            return behavior, config
    return "baseline", PATIENT_BEHAVIORS["baseline"]


def detect_patient_behavior_cues(conversation_history, patient_responses):
    """
    Analyze conversation to detect behavioral cues that inform empathetic responses
    """
    cue_detector = RoleResponder(
        """You are a behavioral psychologist specializing in patient communication patterns.
    Analyze the patient's responses to identify behavioral cues that indicate their communication style and emotional state.
    This will help the doctor provide more empathetic and effective care."""
    )

    recent_responses = patient_responses[-3:]  # Look at last 3 patient responses
    analysis = cue_detector.ask(
        f"""
    Analyze these recent patient responses for behavioral and emotional cues:
    
    {json.dumps(recent_responses, indent=2)}
    
    Identify which of these behavioral patterns are present:
    - Anxiety/fear (catastrophic thinking, worry about serious disease)
    - Embarrassment/hesitation (reluctance to share, vague responses)
    - Stoicism/minimization (downplaying symptoms, "tough" attitude)
    - Confusion/uncertainty (timeline issues, memory problems)
    - Storytelling/context-sharing (excessive details, family stories)
    - Family pressure/caregiver stress
    
    Respond in the following format:
    THINKING: <Your analysis of the patient's communication patterns>
    BEHAVIORAL_CUES: <List the main cues you detect>
    EMPATHY_NEEDS: <What kind of empathetic response would help this patient>
    """
    )

    return analysis


def generate_empathetic_questioning_prompt(
    base_role, behavioral_cues="", turn_stage="early"
):
    """
    Generate questioning prompts that incorporate empathy based on detected behavioral cues
    """
    base_empathy_instructions = """
    You are a compassionate physician who recognizes that patients have different communication styles and emotional needs.
    
    CORE EMPATHY PRINCIPLES:
    - Validate the patient's feelings and concerns
    - Use language that matches the patient's emotional state
    - Build trust through understanding
    - Adapt your communication style to the patient's needs
    """

    stage_specific_guidance = {
        "early": "Focus on building rapport and making the patient feel heard and safe.",
        "middle": "Show understanding of their concerns while gathering focused information.",
        "late": "Provide reassurance and clear communication about next steps.",
    }

    empathy_adaptations = ""
    if "anxiety" in behavioral_cues.lower() or "fear" in behavioral_cues.lower():
        empathy_adaptations += """
        ANXIETY/FEAR DETECTED - Empathetic Adaptations:
        - Acknowledge their fears explicitly: "I can see this is really worrying you..."
        - Provide reassurance: "We're going to figure this out together"
        - Explain your reasoning: "I'm asking this because..."
        - Offer hope: "Many conditions that cause these symptoms are very treatable"
        """

    if "embarrass" in behavioral_cues.lower() or "hesitat" in behavioral_cues.lower():
        empathy_adaptations += """
        EMBARRASSMENT/HESITATION DETECTED - Empathetic Adaptations:
        - Normalize their experience: "This is very common, and there's nothing to be embarrassed about"
        - Create safe space: "Everything we discuss is confidential"
        - Use gentle, non-judgmental language
        - Thank them for sharing: "I appreciate you telling me about this"
        """

    if "minimiz" in behavioral_cues.lower() or "tough" in behavioral_cues.lower():
        empathy_adaptations += """
        STOICISM/MINIMIZATION DETECTED - Empathetic Adaptations:
        - Acknowledge their strength: "I can see you're someone who handles things well"
        - Respect their perspective: "I understand you don't like to make a big deal of things"
        - Frame health-seeking as strength: "Taking care of this shows good judgment"
        - Be direct and practical in your approach
        """

    if "confus" in behavioral_cues.lower() or "uncertain" in behavioral_cues.lower():
        empathy_adaptations += """
        CONFUSION/UNCERTAINTY DETECTED - Empathetic Adaptations:
        - Show patience: "Take your time, there's no rush"
        - Normalize confusion: "It's completely normal to have trouble remembering exact timelines"
        - Break down questions into smaller parts
        - Offer gentle guidance: "Let's start with what you remember most clearly"
        """

    if "story" in behavioral_cues.lower() or "detail" in behavioral_cues.lower():
        empathy_adaptations += """
        STORYTELLING/DETAIL-SHARING DETECTED - Empathetic Adaptations:
        - Show appreciation for context: "Thank you for giving me that background"
        - Gently redirect when needed: "That's helpful context. Let me ask specifically about..."
        - Acknowledge family/social connections they mention
        - Validate their need to provide context
        """

    if "family" in behavioral_cues.lower() or "pressure" in behavioral_cues.lower():
        empathy_adaptations += """
        FAMILY PRESSURE/CAREGIVER STRESS DETECTED - Empathetic Adaptations:
        - Acknowledge family concerns: "I can see your family is worried about you"
        - Validate caregiving burden: "It sounds like you have a lot of responsibility"
        - Include family perspective when appropriate
        - Address both patient and family needs
        """

    combined_prompt = f"""
    {base_empathy_instructions}
    
    CURRENT STAGE: {turn_stage.upper()}
    {stage_specific_guidance[turn_stage]}
    
    {empathy_adaptations if empathy_adaptations else "Use standard empathetic communication approaches."}
    
    COMMUNICATION GUIDELINES:
    - Ask ONE clear question at a time
    - Include empathetic acknowledgment before your question
    - Use warm, professional language
    - Show genuine interest in the patient as a person
    - Validate their experience before seeking more information
    
    {base_role}
    """

    return combined_prompt


def generate_patient_prompt_modifiers(behavior_config, is_initial=True):
    """Generate prompt modifiers based on selected patient behavior"""
    modifiers = behavior_config.get("modifiers", [])

    base_instructions = """You are simulating a real patient in conversation with their doctor. 
Respond naturally and realistically, as if you are experiencing symptoms yourself — but like a real patient, you are NOT medically trained and do NOT understand what's important or what anything means. 
You have NOT spoken to any other doctors. 
You may feel scared, unsure, or even embarrassed. 
You are NOT trying to impress the doctor with a clear answer — just describe what you feel in your own confused way."""

    behavioral_additions = []

    # Information withholding behaviors
    if "embarrassed_symptoms" in modifiers:
        if is_initial:
            behavioral_additions.append(
                "You are embarrassed about certain symptoms (especially those related to bathroom habits, sexual health, mental health, or substance use). You will NOT mention these initially unless directly asked."
            )
        else:
            behavioral_additions.append(
                "If the doctor asks specific questions about areas you were initially embarrassed about, you may gradually reveal more information, but still with some hesitation."
            )

    if "gradual_revelation" in modifiers:
        behavioral_additions.append(
            "You tend to reveal information slowly. Start with the most obvious symptoms and only mention other details if specifically prompted."
        )

    # Anxiety-related behaviors
    if "catastrophic_thinking" in modifiers:
        behavioral_additions.append(
            "You tend to worry that your symptoms mean something terrible. You might mention fears about serious diseases or express anxiety about 'what if' scenarios."
        )

    if "symptom_amplification" in modifiers:
        behavioral_additions.append(
            "You tend to describe symptoms as more severe than they might objectively be. Use words like 'terrible,' 'excruciating,' 'the worst,' or 'unbearable' when describing discomfort."
        )

    if "multiple_concerns" in modifiers:
        behavioral_additions.append(
            "You have several different symptoms or concerns you're worried about. You might jump between different issues or mention seemingly unrelated symptoms."
        )

    # Stoic/minimizing behaviors
    if "symptom_minimization" in modifiers:
        behavioral_additions.append(
            "You tend to downplay your symptoms. Use phrases like 'it's probably nothing,' 'I don't want to make a big deal,' or 'it's not that bad.' You might mention that others told you to come in."
        )

    if "delayed_care_seeking" in modifiers:
        behavioral_additions.append(
            "You mention that you've been dealing with this for a while before coming in. You might say things like 'I thought it would go away' or 'I've been putting this off.'"
        )

    if "tough_attitude" in modifiers:
        behavioral_additions.append(
            "You pride yourself on being tough and not complaining. You might mention how you usually don't go to doctors or how you can 'handle pain.'"
        )

    # Chronology and memory issues
    if "timeline_confusion" in modifiers:
        behavioral_additions.append(
            "You're not entirely sure about when symptoms started or how they've progressed. You might say things like 'I think it was last week... or maybe two weeks ago?' or mix up the order of events."
        )

    if "sequence_uncertainty" in modifiers:
        behavioral_additions.append(
            "You're unclear about which symptoms came first or how they're related. You might contradict yourself slightly about the timeline."
        )

    # Tangential behaviors
    if "excessive_details" in modifiers:
        behavioral_additions.append(
            "You tend to include lots of potentially irrelevant details about your day, what you were doing when symptoms started, or other life circumstances."
        )

    if "family_stories" in modifiers:
        behavioral_additions.append(
            "You mention family members who had similar symptoms or relate your symptoms to things that happened to relatives or friends."
        )

    if "tangential_information" in modifiers:
        behavioral_additions.append(
            "You sometimes go off on tangents about work stress, family issues, or other life events that may or may not be related to your symptoms."
        )

    # Family involvement
    if "family_influence" in modifiers:
        behavioral_additions.append(
            "You mention that a family member (spouse, parent, child) is worried about you and may have influenced your decision to come in. You might reference their concerns."
        )

    if "secondary_concerns" in modifiers:
        behavioral_additions.append(
            "You express concerns about how your symptoms affect your family or your ability to take care of others."
        )

    # Add empathy responsiveness
    empathy_response_instruction = """
    
    EMPATHY RESPONSIVENESS:
    - If the doctor shows understanding or validation, you feel more comfortable sharing
    - If the doctor seems rushed or dismissive, you become more guarded
    - When the doctor explains things clearly, you feel more at ease
    - If the doctor acknowledges your concerns, you're more likely to open up
    - Respond positively to warmth and genuine interest in your wellbeing
    """

    # Combine base instructions with behavioral modifiers
    full_instructions = base_instructions
    if behavioral_additions:
        full_instructions += (
            "\n\nSPECIFIC BEHAVIORAL TRAITS for this interaction:\n"
            + "\n".join(f"- {trait}" for trait in behavioral_additions)
        )

    full_instructions += empathy_response_instruction

    return full_instructions


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
# Patient will be dynamically created with behavior-specific instructions
summarizer = RoleResponder(
    "You are a clinical summarizer trained to extract structured vignettes from doctor–patient dialogues."
)

diagnoser = RoleResponder("You are a board-certified diagnostician.")

# === Store all transcripts ===
summarizer_outputs = []
diagnosing_doctor_outputs = []
questioning_doctor_outputs = []
patient_response = []
conversation = []
behavioral_analyses = []


def run_vignette_task(args):
    idx, vignette_text, disease = args
    global conversation, patient_response, summarizer_outputs, diagnosing_doctor_outputs, questioning_doctor_outputs, treatment_plans, behavioral_analyses
    conversation = []
    patient_response = []
    summarizer_outputs = []
    diagnosing_doctor_outputs = []
    questioning_doctor_outputs = []
    treatment_plans = []
    behavioral_analyses = []
    return process_vignette(idx, vignette_text, disease)


if __name__ == "__main__":
    # Remove and recreate output directories to start empty
    output_dirs = [
        "2summarizer_outputs",
        "2patient_followups",
        "2diagnosing_doctor_outputs",
        "2questioning_doctor_outputs",
        "2treatment_plans",
        "2behavior_metadata",
        "2behavioral_analyses",
        "2accuracy_evaluations",  # New directory for diagnostic accuracy tracking
    ]
    for directory in output_dirs:
        if os.path.exists(directory):
            shutil.rmtree(directory)
        os.makedirs(directory, exist_ok=True)

    with open(
        "new_data_gen/actual_data_gen/medical_vignettes_100_diseases.json",
        "r",
    ) as f:
        vignette_dict = json.load(f)

    flattened_vignettes = []
    for disease, vignettes in vignette_dict.items():
        # Only process if we have a list of vignettes
        if not isinstance(vignettes, list):
            continue
        for vignette in vignettes:  # Only take the first 2
            flattened_vignettes.append((disease, vignette))

    # Launch multiprocessing pool with 12 workers
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
    all_behavior_metadata = []
    all_behavioral_analyses = []

    for result in results:
        all_patient_followups.extend(result["patient_response"])
        all_summarizer_outputs.extend(result["summarizer_outputs"])
        all_diagnosing_doctor_outputs.extend(result["diagnosing_doctor_outputs"])
        all_questioning_doctor_outputs.extend(result["questioning_doctor_outputs"])
        all_treatment_plans.extend(result["treatment_plans"])
        all_behavior_metadata.append(result["behavior_metadata"])
        all_behavioral_analyses.extend(result["behavioral_analyses"])

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
    with open("2behavior_metadata.json", "w") as f:
        json.dump(all_behavior_metadata, f, indent=2)
    with open("2behavioral_analyses.json", "w") as f:
        json.dump(all_behavioral_analyses, f, indent=2)

    print(
        "\n✅ All role outputs saved with gold diagnosis guidance and empathetic behavioral adaptations."
    )

    # Print behavior distribution summary
    behavior_counts = {}
    for metadata in all_behavior_metadata:
        behavior_type = metadata["behavior_type"]
        behavior_counts[behavior_type] = behavior_counts.get(behavior_type, 0) + 1

    print("\n📊 Patient Behavior Distribution:")
    for behavior, count in behavior_counts.items():
        percentage = (count / len(all_behavior_metadata)) * 100
        print(f"  {behavior}: {count} cases ({percentage:.1f}%)")

    # Print diagnostic accuracy summary
    total_cases = len(all_diagnosing_doctor_outputs)
    accurate_diagnoses = sum(
        1
        for output in all_diagnosing_doctor_outputs
        if output.get("accuracy_evaluation", {}).get("gold_diagnosis_found", False)
    )

    print(f"\n🎯 DIAGNOSTIC ACCURACY SUMMARY:")
    print(f"   Total cases processed: {total_cases}")
    print(f"   Gold diagnosis found: {accurate_diagnoses}")
    print(
        f"   Overall accuracy: {(accurate_diagnoses/total_cases)*100:.1f}%"
        if total_cases > 0
        else "   No cases processed"
    )

    # Print accuracy by stage
    stages = {"E": "Early", "M": "Middle", "L": "Late"}
    for stage_letter, stage_name in stages.items():
        stage_cases = [
            output
            for output in all_diagnosing_doctor_outputs
            if output.get("letter") == stage_letter
        ]
        stage_accurate = sum(
            1
            for case in stage_cases
            if case.get("accuracy_evaluation", {}).get("gold_diagnosis_found", False)
        )
        if stage_cases:
            stage_accuracy = (stage_accurate / len(stage_cases)) * 100
            print(
                f"   {stage_name} stage accuracy: {stage_accuracy:.1f}% ({stage_accurate}/{len(stage_cases)})"
            )

    # Print empathy adaptation summary
    empathy_adaptations = {}
    for analysis in all_behavioral_analyses:
        if "EMPATHY_NEEDS:" in analysis["analysis"]:
            empathy_need = (
                analysis["analysis"].split("EMPATHY_NEEDS:")[1].strip()[:50] + "..."
            )
            empathy_adaptations[empathy_need] = (
                empathy_adaptations.get(empathy_need, 0) + 1
            )

    print("\n💝 Top Empathy Adaptations Used:")
    sorted_adaptations = sorted(
        empathy_adaptations.items(), key=lambda x: x[1], reverse=True
    )
    for adaptation, count in sorted_adaptations[:5]:
        print(f"  {adaptation}: {count} times")

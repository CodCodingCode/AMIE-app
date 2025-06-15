import os
import json
from openai import OpenAI
import time
import multiprocessing
import shutil
from itertools import islice
import random
from prompts import (
    PATIENT_BEHAVIORS,
    PATIENT_INTERPRETER_ROLE_INSTRUCTION,
    PATIENT_INTERPRETATION_PROMPT,
    BEHAVIOR_CUE_DETECTOR_ROLE_INSTRUCTION,
    BEHAVIOR_CUE_DETECTION_PROMPT,
    UNBIASED_VIGNETTE_SUMMARIZER_ROLE_INSTRUCTION,
    UNBIASED_VIGNETTE_GENERATION_PROMPT,
    EARLY_DIAGNOSIS_PROMPT,
    MIDDLE_DIAGNOSIS_PROMPT,
    LATE_DIAGNOSIS_PROMPT,
    TREATMENT_PLAN_PROMPT,
    EARLY_EXPLORATION_QUESTIONING_ROLE,
    FOCUSED_CLARIFICATION_QUESTIONING_ROLE,
    DIAGNOSTIC_CONFIRMATION_QUESTIONING_ROLE,
    INITIAL_PATIENT_RESPONSE_PROMPT,
    FOLLOWUP_PATIENT_RESPONSE_PROMPT,
    BASE_PATIENT_INSTRUCTIONS,
    generate_patient_prompt_modifiers,
    TEST_RESULT_GENERATOR_ROLE,
    TEST_RESULT_GENERATION_PROMPT,
    VIGNETTE_UPDATE_WITH_TEST_RESULTS_PROMPT,
    MODIFIED_QUESTION_GENERATION_PROMPT,
)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
model = "gpt-4.1-nano"

treatment_plans = []


def generate_guided_questioner_prompt(base_prompt, gold_diagnosis, current_vignette):
    """Generate questioning prompts without gold diagnosis guidance"""
    return base_prompt


# === Test Result Generation ===
def generate_test_results(requested_test, gold_diagnosis, current_vignette):
    """Generate realistic test results that support the gold diagnosis"""
    
    test_generator = RoleResponder(TEST_RESULT_GENERATOR_ROLE)
    
    prompt = TEST_RESULT_GENERATION_PROMPT.format(
        gold_diagnosis=gold_diagnosis,
        current_vignette=current_vignette,
        requested_test=requested_test
    )
    
    return test_generator.ask(prompt)


# === Patient Interpreter Class (Modified to handle test results) ===
class PatientInterpreter:
    """Agent specialized in reading patient communication patterns and extracting unbiased clinical information using Chain of Thought reasoning"""

    def __init__(self):
        self.role_instruction = PATIENT_INTERPRETER_ROLE_INSTRUCTION
        self.responder = RoleResponder(self.role_instruction)

    def interpret_patient_communication(
        self, conversation_history, detected_behavior, current_vignette, is_test_result=False
    ):
        """Analyze patient communication to extract unbiased clinical information using Chain of Thought reasoning
        
        Skip interpretation for test results since they're objective data"""
        
        if is_test_result:
            # For test results, return a simple pass-through interpretation
            return {
                "raw": "THINKING: This is objective test result data that requires no behavioral interpretation.\nANSWER: Test results are objective medical data.",
                "clean": "Test results are objective medical data."
            }

        interpretation_prompt = PATIENT_INTERPRETATION_PROMPT.format(
            detected_behavior=detected_behavior,
            conversation_history=json.dumps(conversation_history[-6:], indent=2),
            current_vignette=current_vignette,
        )

        return self.responder.ask(interpretation_prompt)


# Enhanced Chain of Thought detect_patient_behavior_cues function (Modified)
def detect_patient_behavior_cues_enhanced(conversation_history, patient_responses, is_test_result=False):
    """Enhanced version that provides more detailed behavioral analysis using Chain of Thought reasoning
    
    Skip analysis for test results since they're objective data"""
    
    if is_test_result:
        # For test results, return a simple pass-through analysis
        return {
            "raw": "THINKING: This is objective test result data that requires no behavioral analysis.\nANSWER: Test results are objective medical data with no behavioral patterns to analyze.",
            "clean": "Test results are objective medical data with no behavioral patterns to analyze."
        }

    cue_detector = RoleResponder(BEHAVIOR_CUE_DETECTOR_ROLE_INSTRUCTION)

    recent_responses = patient_responses[-3:]

    analysis = cue_detector.ask(
        BEHAVIOR_CUE_DETECTION_PROMPT.format(
            recent_responses=json.dumps(recent_responses, indent=2),
            conversation_history=json.dumps(conversation_history[-6:], indent=2),
        )
    )

    return analysis


# Enhanced summarizer function that incorporates patient interpretation (Modified)
def generate_unbiased_vignette(
    conversation_history, previous_vignette, patient_interpretation, is_test_result=False
):
    """Generate a vignette that accounts for patient communication biases"""

    unbiased_summarizer = RoleResponder(UNBIASED_VIGNETTE_SUMMARIZER_ROLE_INSTRUCTION)

    if is_test_result:
        # For test results, focus on incorporating objective data
        summary_prompt = VIGNETTE_UPDATE_WITH_TEST_RESULTS_PROMPT.format(
            conversation_history=json.dumps(conversation_history, indent=2),
            previous_vignette=previous_vignette,
        )
    else:
        summary_prompt = UNBIASED_VIGNETTE_GENERATION_PROMPT.format(
            conversation_history=json.dumps(conversation_history, indent=2),
            previous_vignette=previous_vignette,
            patient_interpretation=patient_interpretation,
        )

    return unbiased_summarizer.ask(summary_prompt)


# === Diagnosis Logic with Cleaning ===
def get_diagnosis_response(
    turn_count, gold_label, vignette_summary, previous_questions, diagnoser
):
    """Get diagnosis with proper stage-based prompting"""
    if turn_count < 4:  # First 2 turns (0, 2)
        base_prompt = EARLY_DIAGNOSIS_PROMPT
        stage = "early"
    elif turn_count >= 4 and turn_count < 8:  # Next 2 turns (4, 6)
        base_prompt = MIDDLE_DIAGNOSIS_PROMPT
        stage = "middle"
    else:  # Last 1 turn (8)
        base_prompt = LATE_DIAGNOSIS_PROMPT
        stage = "late"

    # Get response from diagnoser (NO GUIDANCE ADDED)
    response = diagnoser.ask(
        base_prompt.format(
            prev_questions=json.dumps(previous_questions),
            vignette=vignette_summary,
            turn_count=turn_count,
        )
    )

    return response


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


# === ROBUST TEST REQUEST PARSING ===
def parse_questioner_response_robust(response_text):
    """
    Robust parser that handles multiple test request formats and patterns
    """
    
    # Initialize defaults
    test_request = False
    requested_test = "None"
    question = response_text.strip()
    
    print(f"\n🔍 PARSING QUESTIONER RESPONSE:")
    print(f"Input length: {len(response_text)} chars")
    print(f"First 300 chars: {response_text[:300]}...")
    
    try:
        # Method 1: Look for explicit TEST_REQUEST format
        if "TEST_REQUEST:" in response_text:
            lines = response_text.strip().split('\n')
            for line in lines:
                line = line.strip()
                
                if line.startswith("TEST_REQUEST:"):
                    test_value = line.split(":", 1)[1].strip().lower()
                    test_request = test_value in ["yes", "true", "1"]
                    print(f"✅ Found TEST_REQUEST: {test_request}")
                
                elif line.startswith("REQUESTED_TEST:"):
                    requested_test = line.split(":", 1)[1].strip()
                    if requested_test.lower() in ["none", "n/a", ""]:
                        requested_test = "None"
                    print(f"✅ Found REQUESTED_TEST: '{requested_test}'")
                
                elif line.startswith("QUESTION:"):
                    question = line.split(":", 1)[1].strip()
                    print(f"✅ Found QUESTION: '{question[:50]}...'")
            
            # Handle single-line format: "TEST_REQUEST: Yes REQUESTED_TEST: XYZ QUESTION: ABC"
            if not test_request:
                for line in lines:
                    if "TEST_REQUEST:" in line and "REQUESTED_TEST:" in line:
                        parts = line.split()
                        for i, part in enumerate(parts):
                            if part == "TEST_REQUEST:" and i + 1 < len(parts):
                                test_request = parts[i + 1].lower() in ["yes", "true", "1"]
                                print(f"✅ Single-line TEST_REQUEST: {test_request}")
                            elif part == "REQUESTED_TEST:" and i + 1 < len(parts):
                                # Collect test name (might be multiple words)
                                test_parts = []
                                for j in range(i + 1, len(parts)):
                                    if parts[j].startswith("QUESTION:"):
                                        break
                                    test_parts.append(parts[j])
                                if test_parts:
                                    requested_test = " ".join(test_parts)
                                    print(f"✅ Single-line REQUESTED_TEST: '{requested_test}'")
                            elif part == "QUESTION:" and i + 1 < len(parts):
                                question_parts = parts[i + 1:]
                                question = " ".join(question_parts)
                                print(f"✅ Single-line QUESTION: '{question[:50]}...'")
        
        # Method 2: Look for test indicators in THINKING section
        if not test_request and "THINKING:" in response_text:
            thinking_section = response_text.split("THINKING:")[1]
            if "ANSWER:" in thinking_section:
                thinking_section = thinking_section.split("ANSWER:")[0]
            
            # Check for test-related keywords in thinking
            test_indicators = [
                "diagnostic testing",
                "testing would be",
                "test would be",
                "examination",
                "fluorescein",
                "slit-lamp",
                "CT scan",
                "MRI",
                "ultrasound",
                "blood test",
                "culture",
                "biopsy"
            ]
            
            thinking_lower = thinking_section.lower()
            for indicator in test_indicators:
                if indicator in thinking_lower:
                    test_request = True
                    print(f"✅ Found test indicator in THINKING: '{indicator}'")
                    break
        
        # Method 3: Look for test requests in the question/answer text
        if not test_request:
            question_lower = question.lower()
            test_phrases = [
                "examination",
                "test",
                "scan",
                "imaging",
                "lab",
                "culture",
                "fluorescein",
                "slit lamp",
                "ct",
                "mri",
                "ultrasound",
                "blood work"
            ]
            
            for phrase in test_phrases:
                if phrase in question_lower:
                    test_request = True
                    print(f"✅ Found test phrase in question: '{phrase}'")
                    break
        
        # Method 4: Extract test name from various locations
        if test_request and requested_test == "None":
            # Look in the full response for test names
            full_text_lower = response_text.lower()
            
            # Common test patterns
            test_patterns = {
                "fluorescein": "Fluorescein staining",
                "slit-lamp": "Slit-lamp examination", 
                "slit lamp": "Slit-lamp examination",
                "ct scan": "CT scan",
                "mri": "MRI",
                "ultrasound": "Ultrasound",
                "culture": "Culture",
                "blood test": "Blood test",
                "examination": "Physical examination"
            }
            
            for pattern, test_name in test_patterns.items():
                if pattern in full_text_lower:
                    requested_test = test_name
                    print(f"✅ Extracted test name: '{test_name}' from pattern '{pattern}'")
                    break
        
        # Method 5: Clean up the question text
        if "ANSWER:" in response_text:
            answer_section = response_text.split("ANSWER:", 1)[1].strip()
            
            # Remove TEST_REQUEST and REQUESTED_TEST lines from question
            answer_lines = answer_section.split('\n')
            clean_lines = []
            
            for line in answer_lines:
                line_stripped = line.strip()
                if not line_stripped.startswith(("TEST_REQUEST:", "REQUESTED_TEST:")):
                    if line_stripped.startswith("QUESTION:"):
                        clean_lines.append(line_stripped.split(":", 1)[1].strip())
                    elif line_stripped and not line_stripped.startswith(("THINKING:", "ANSWER:")):
                        clean_lines.append(line_stripped)
            
            if clean_lines:
                question = " ".join(clean_lines).strip()
        
        # Final cleanup
        if not question or question == response_text:
            # Extract the cleanest sentence as fallback
            sentences = response_text.replace('\n', ' ').split('.')
            for sentence in sentences:
                sentence = sentence.strip()
                if (sentence and 
                    len(sentence) > 10 and 
                    not sentence.startswith(("THINKING", "ANSWER", "TEST_REQUEST", "REQUESTED_TEST"))):
                    question = sentence
                    break
        
        print(f"🎯 FINAL RESULTS:")
        print(f"   test_request: {test_request}")
        print(f"   requested_test: '{requested_test}'")
        print(f"   question: '{question[:100]}...'")
        
    except Exception as e:
        print(f"❌ Error in robust parsing: {e}")
        # Ultra-safe fallback
        question = response_text.strip()
    
    return test_request, requested_test, question


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

    prompt = INITIAL_PATIENT_RESPONSE_PROMPT.format(
        patient_instructions=patient_instructions,
        response_length=response_length,
        age_gender_instruction=age_gender_instruction,
        vignette_text=vignette_text,
        initial_prompt=initial_prompt,
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
            "output": raw_patient,  # Store the full THINKING + ANSWER
            "behavior_type": behavior_type,
            "behavior_config": behavior_config,
            "gold_diagnosis": gold_label,
        }
    )

    while not diagnosis_complete:

        # Check if the last patient response was a test result
        is_test_result = len(patient_response) > 1 and patient_response[-1].get("is_test_result", False)

        behavioral_result = detect_patient_behavior_cues_enhanced(
            conversation, patient_response, is_test_result=is_test_result
        )
        behavioral_analysis_raw = behavioral_result["raw"]
        behavioral_analysis = behavioral_result["clean"]

        behavioral_analyses.append(
            {
                "vignette_index": idx,
                "turn_count": turn_count,
                "analysis": behavioral_analysis_raw,  # Store full version
            }
        )

        # Patient Interpretation (Modified)
        patient_interpreter = PatientInterpreter()

        interpretation_result = patient_interpreter.interpret_patient_communication(
            conversation, behavioral_analysis, prev_vignette_summary, is_test_result=is_test_result
        )
        patient_interpretation_raw = interpretation_result["raw"]
        patient_interpretation = interpretation_result["clean"]

        patient_interpretations.append(
            {
                "vignette_index": idx,
                "turn_count": turn_count,
                "interpretation": patient_interpretation_raw,  # Store full version
            }
        )
        print(f"🔍 Patient Interpretation: {patient_interpretation}...")

        # Generate unbiased vignette using interpreter insights (Modified)
        joined_conversation = "\\n".join(conversation)

        # Create input for summarizer
        summarizer_input = f"CONVERSATION HISTORY:\n{json.dumps(conversation, indent=2)}\n\nPREVIOUS VIGNETTE:\n{prev_vignette_summary}\n\nPATIENT COMMUNICATION ANALYSIS:\n{patient_interpretation}"

        # 🔍 DEBUG: Print summarizer input
        print(f"\n📝 SUMMARIZER INPUT:")
        print("=" * 40)
        print(f"Previous vignette length: {len(prev_vignette_summary)} chars")
        print(f"Previous vignette preview: {prev_vignette_summary[:100]}...")
        print(f"Patient interpretation length: {len(patient_interpretation)} chars")
        print("=" * 40)

        vignette_result = generate_unbiased_vignette(
            conversation, prev_vignette_summary, patient_interpretation, is_test_result=is_test_result
        )
        vignette_summary_raw = vignette_result["raw"]
        vignette_summary = vignette_result[
            "clean"
        ]  # This is what gets passed to next agents

        # 🔍 DEBUG: Print summarizer results
        print(f"\n📊 SUMMARIZER RESULTS:")
        print("=" * 40)
        print(f"Raw result length: {len(vignette_summary_raw)} chars")
        print(f"Raw result preview: {vignette_summary_raw[:200]}...")
        print(f"Clean result length: {len(vignette_summary)} chars")
        print(f"Clean result preview: {vignette_summary[:200]}...")
        print("=" * 40)

        # Also add a check for the corrupted state
        if "Unable to extract answer content properly" in vignette_summary:
            print(f"❌ CORRUPTED VIGNETTE DETECTED!")
            print(f"Setting fallback vignette...")
            vignette_summary = f"Patient presents with eye symptoms including redness, swelling, and tearing. Symptoms began approximately 2 days ago after playing soccer."

        summarizer_outputs.append(
            {
                "vignette_index": idx,
                "input": summarizer_input,
                "output": vignette_summary_raw,  # Store full version
                "turn_count": turn_count,
                "gold_diagnosis": gold_label,
            }
        )

        prev_vignette_summary = vignette_summary

        if "ANSWER:" in vignette_summary:
            vignette_summary = vignette_summary.split("ANSWER:")[1].strip()
        else:
            vignette_summary = vignette_summary

        # === UPDATED DIAGNOSIS LOGIC WITH CLEANING ===

        print("Turn count:", turn_count)
        letter = ""
        stage = "early"
        if turn_count < 4:  # First 2 turns
            letter = "E"
            stage = "early"
        elif turn_count >= 4 and turn_count < 8:  # Next 2 turns
            letter = "M"
            stage = "middle"
        elif turn_count >= 8:  # Last 1 turn
            letter = "L"
            stage = "late"

        diagnosis_result = get_diagnosis_response(
            turn_count, gold_label, vignette_summary, previous_questions, diagnoser
        )
        diagnosis_raw = diagnosis_result["raw"]
        diagnosis = diagnosis_result["clean"]  # This is what gets passed to next agents

        diagnosing_doctor_outputs.append(
            {
                "vignette_index": idx,
                "input": vignette_summary,
                "output": diagnosis_raw,  # Store full version
                "turn_count": turn_count,
                "letter": letter,
                "gold_diagnosis": gold_label,
            }
        )

        # Handle END signal explicitly
        if "END" in diagnosis:
            if turn_count >= 8:
                diagnosis_complete = True
                print(f"✅ Reached END for vignette {idx}. Moving to next.\n")
                prompt = TREATMENT_PLAN_PROMPT.format(
                    diagnosis=diagnosis,
                    gold_label=gold_label,
                    vignette_summary=vignette_summary,
                    behavior_type=behavior_type,
                )

                treatment_result = diagnoser.ask(prompt)
                raw_treatment = treatment_result["raw"]

                treatment_plans.append(
                    {
                        "vignette_index": idx,
                        "input": diagnosis,
                        "output": raw_treatment,  # Store full version
                        "gold_diagnosis": gold_label,
                    }
                )
                break

        # Limit to last 3–5 doctor questions
        previous_questions = [
            entry.replace("DOCTOR:", "").strip()
            for entry in conversation
            if entry.startswith("DOCTOR:")
        ][-5:]

        # === QUESTIONING WITH ROBUST TEST REQUEST DETECTION ===
        base_questioning_role = ""
        if turn_count < 4:
            base_questioning_role = EARLY_EXPLORATION_QUESTIONING_ROLE

        elif turn_count >= 4 and turn_count < 8:
            base_questioning_role = FOCUSED_CLARIFICATION_QUESTIONING_ROLE

        else:
            base_questioning_role = DIAGNOSTIC_CONFIRMATION_QUESTIONING_ROLE

        # Add gold diagnosis guidance to questioning
        guided_questioning_role = generate_guided_questioner_prompt(
            base_questioning_role, gold_label, vignette_summary
        )

        # Create questioner with enhanced role definition
        questioner = RoleResponder(guided_questioning_role)

        # Use modified prompt with test request detection
        prompt = MODIFIED_QUESTION_GENERATION_PROMPT.format(
            previous_questions=json.dumps(previous_questions),
            interview_phase="EARLY EXPLORATION"
            if turn_count < 6
            else "FOCUSED CLARIFICATION"
            if turn_count < 11
            else "DIAGNOSTIC CONFIRMATION",
            vignette_summary=vignette_summary,
            diagnosis=diagnosis,
            behavioral_analysis=behavioral_analysis,
            turn_count=turn_count,
        )

        followup_result = questioner.ask(prompt)
        raw_followup = followup_result["raw"]
        followup_clean = followup_result["clean"]

        # ✅ FIXED: Use robust parsing function
        test_request, requested_test, followup_question = parse_questioner_response_robust(followup_clean)

        print("❓ Doctor's Request:", followup_question)
        if test_request:
            print(f"🧪 Test Requested: {requested_test}")

        questioning_doctor_outputs.append(
            {
                "vignette_index": idx,
                "input": vignette_summary + diagnosis + behavioral_analysis,
                "output": raw_followup,  # Store full version
                "letter": letter,
                "behavioral_cues": behavioral_analysis,
                "test_request": test_request,
                "requested_test": requested_test,
                "gold_diagnosis": gold_label,
            }
        )
        conversation.append(f"DOCTOR: {followup_question}")

        # === PATIENT RESPONSE: Test Results vs Normal Response ===
        if test_request and requested_test != "None":
            # Generate test results instead of normal patient response
            test_result = generate_test_results(requested_test, gold_label, vignette_summary)
            test_result_raw = test_result["raw"]
            test_result_clean = test_result["clean"]
            
            print("🧪 Test Results:", test_result_clean)
            conversation.append(f"PATIENT: {test_result_clean}")
            
            patient_response.append(
                {
                    "vignette_index": idx,
                    "input": f"{vignette_text}\n{followup_question}\n{requested_test}",
                    "output": test_result_raw,  # Store full version
                    "behavior_type": "test_result",
                    "turn_count": turn_count,
                    "is_test_result": True,
                    "test_type": requested_test,
                    "gold_diagnosis": gold_label,
                }
            )
        else:
            # Normal patient response with behavioral patterns
            
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
            prompt = FOLLOWUP_PATIENT_RESPONSE_PROMPT.format(
                patient_followup_instructions=patient_followup_instructions,
                behavior_type=behavior_type,
                vignette_text=vignette_text,
                followup_question=followup_question,
                response_guidance=response_guidance,
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
                    "output": raw_patient_fb,  # Store full version
                    "behavior_type": behavior_type,
                    "turn_count": turn_count,
                    "is_test_result": False,
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


class RoleResponder:
    def __init__(self, role_instruction):
        self.role_instruction = (
            role_instruction
            + """
        
        CRITICAL FORMAT REQUIREMENT: You MUST always respond in this format:
        
        THINKING: [your reasoning]
        ANSWER: [your actual response]
        
        Start every response with "THINKING:" - this is non-negotiable.
        """
        )

    def ask(self, user_input, max_retries=3):
        """Ask with guaranteed THINKING/ANSWER format and return both raw and clean outputs"""

        for attempt in range(max_retries):
            messages = [
                {"role": "system", "content": self.role_instruction},
                {"role": "user", "content": user_input},
            ]

            response = client.chat.completions.create(model=model, messages=messages)
            raw_response = response.choices[0].message.content.strip()

            # 🔍 DEBUG: Print the raw GPT response
            print(f"\n🤖 RAW GPT RESPONSE (attempt {attempt + 1}):")
            print("=" * 50)
            print(raw_response)
            print("=" * 50)

            # Clean and normalize the response
            cleaned_response = self.clean_thinking_answer_format(raw_response)

            # 🔍 DEBUG: Print the cleaned response
            print(f"\n🧹 CLEANED RESPONSE:")
            print("=" * 30)
            print(cleaned_response)
            print("=" * 30)

            # Validate the cleaned response
            if self.validate_thinking_answer_format(cleaned_response):
                # Extract just the ANSWER portion for the clean output
                answer_only = self.extract_answer_only(cleaned_response)

                # 🔍 DEBUG: Print the extracted answer
                print(f"\n✅ EXTRACTED ANSWER:")
                print("=" * 20)
                print(answer_only)
                print("=" * 20)

                return {
                    "raw": cleaned_response,  # Full THINKING: + ANSWER:
                    "clean": answer_only,  # Just the answer content
                }
            else:
                # 🔍 DEBUG: Print validation failure
                print(f"\n❌ VALIDATION FAILED for attempt {attempt + 1}")
                print(f"Cleaned response: {cleaned_response[:200]}...")

        # Final fallback
        fallback_raw = f"THINKING: Format enforcement failed after {max_retries} attempts\nANSWER: Unable to get properly formatted response."
        fallback_clean = "Unable to get properly formatted response."

        # 🔍 DEBUG: Print fallback
        print(f"\n💥 FALLBACK TRIGGERED after {max_retries} attempts")
        print(f"Final raw response was: {raw_response[:200]}...")

        return {"raw": fallback_raw, "clean": fallback_clean}

    def extract_answer_only(self, text):
        """Extract just the content after ANSWER:"""
        if "ANSWER:" in text:
            extracted = text.split("ANSWER:", 1)[1].strip()
            # 🔍 DEBUG: Print extraction process
            print(f"\n🎯 EXTRACTING ANSWER from: {text[:100]}...")
            print(f"🎯 EXTRACTED: {extracted[:100]}...")
            return extracted

        # 🔍 DEBUG: No ANSWER found
        print(f"\n⚠️ NO 'ANSWER:' found in text: {text[:100]}...")
        return text.strip()

    def clean_thinking_answer_format(self, text):
        """Clean and ensure exactly one THINKING and one ANSWER section"""

        # 🔍 DEBUG: Print input to cleaning function
        print(f"\n🧼 CLEANING INPUT:")
        print(f"Input length: {len(text)} characters")
        print(f"First 200 chars: {text[:200]}...")
        print(f"Contains THINKING: {'THINKING:' in text}")
        print(f"Contains ANSWER: {'ANSWER:' in text}")

        # Remove any leading/trailing whitespace
        text = text.strip()

        # Find all THINKING and ANSWER positions
        thinking_positions = []
        answer_positions = []

        lines = text.split("\n")
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            if line_stripped.startswith("THINKING:"):
                thinking_positions.append(i)
                print(f"🧠 Found THINKING at line {i}: {line_stripped[:50]}...")
            elif line_stripped.startswith("ANSWER:"):
                answer_positions.append(i)
                print(f"💬 Found ANSWER at line {i}: {line_stripped[:50]}...")

        print(f"📊 THINKING positions: {thinking_positions}")
        print(f"📊 ANSWER positions: {answer_positions}")

        # If we have exactly one of each, check if they're in the right order
        if len(thinking_positions) == 1 and len(answer_positions) == 1:
            thinking_idx = thinking_positions[0]
            answer_idx = answer_positions[0]

            if thinking_idx < answer_idx:
                print(f"✅ Perfect format detected!")
                # Perfect format, just clean up the content
                thinking_content = lines[thinking_idx][9:].strip()  # Remove "THINKING:"
                answer_content = []

                # Collect thinking content (everything between THINKING and ANSWER)
                for i in range(thinking_idx + 1, answer_idx):
                    thinking_content += " " + lines[i].strip()

                # Collect answer content (everything after ANSWER)
                answer_content = lines[answer_idx][7:].strip()  # Remove "ANSWER:"
                for i in range(answer_idx + 1, len(lines)):
                    answer_content += " " + lines[i].strip()

                result = f"THINKING: {thinking_content.strip()}\nANSWER: {answer_content.strip()}"
                print(f"✅ Perfect format result: {result[:100]}...")
                return result

        print(f"⚠️ Format needs fixing...")

        # If format is messed up, try to extract and rebuild
        # Look for the first THINKING and first ANSWER after it
        thinking_content = ""
        answer_content = ""

        first_thinking = -1
        first_answer_after_thinking = -1

        for i, line in enumerate(lines):
            line_stripped = line.strip()
            if line_stripped.startswith("THINKING:") and first_thinking == -1:
                first_thinking = i
                thinking_content = line_stripped[9:].strip()
                print(f"🎯 Using THINKING from line {i}")
            elif (
                line_stripped.startswith("ANSWER:")
                and first_thinking != -1
                and first_answer_after_thinking == -1
            ):
                first_answer_after_thinking = i
                answer_content = line_stripped[7:].strip()
                print(f"🎯 Using ANSWER from line {i}")
                break
            elif first_thinking != -1 and first_answer_after_thinking == -1:
                # Still collecting thinking content
                thinking_content += " " + line_stripped

        # Collect remaining answer content
        if first_answer_after_thinking != -1:
            for i in range(first_answer_after_thinking + 1, len(lines)):
                line_stripped = lines[i].strip()
                # Stop if we hit another THINKING or ANSWER
                if line_stripped.startswith("THINKING:") or line_stripped.startswith(
                    "ANSWER:"
                ):
                    break
                answer_content += " " + line_stripped

        print(f"🔧 Extracted thinking: {thinking_content[:50]}...")
        print(f"🔧 Extracted answer: {answer_content[:50]}...")

        # If we still don't have both parts, try to extract from the raw text
        if not thinking_content or not answer_content:
            print(f"🆘 Last resort extraction...")
            # Last resort: split on the patterns
            if "THINKING:" in text and "ANSWER:" in text:
                parts = text.split("ANSWER:", 1)
                if len(parts) == 2:
                    thinking_part = parts[0]
                    answer_part = parts[1]

                    # Extract thinking content
                    if "THINKING:" in thinking_part:
                        thinking_content = thinking_part.split("THINKING:", 1)[
                            1
                        ].strip()

                    # Clean answer content (remove any nested THINKING/ANSWER)
                    answer_lines = answer_part.split("\n")
                    clean_answer_lines = []
                    for line in answer_lines:
                        if not line.strip().startswith(
                            "THINKING:"
                        ) and not line.strip().startswith("ANSWER:"):
                            clean_answer_lines.append(line)
                    answer_content = " ".join(clean_answer_lines).strip()

        # Fallback if we still don't have proper content
        if not thinking_content:
            print(f"❌ Failed to extract thinking content")
            thinking_content = "Unable to extract thinking content properly"
        if not answer_content:
            print(f"❌ Failed to extract answer content")
            answer_content = "Unable to extract answer content properly"

        final_result = (
            f"THINKING: {thinking_content.strip()}\nANSWER: {answer_content.strip()}"
        )
        print(f"🏁 Final cleaned result: {final_result[:100]}...")
        return final_result

    def validate_thinking_answer_format(self, text):
        """Validate that the text has exactly one THINKING and one ANSWER in correct order"""
        lines = text.split("\n")

        thinking_count = 0
        answer_count = 0
        thinking_first = False

        for line in lines:
            line_stripped = line.strip()
            if line_stripped.startswith("THINKING:"):
                thinking_count += 1
                if answer_count == 0:  # No ANSWER seen yet
                    thinking_first = True
            elif line_stripped.startswith("ANSWER:"):
                answer_count += 1

        is_valid = thinking_count == 1 and answer_count == 1 and thinking_first
        print(
            f"✅ VALIDATION: thinking_count={thinking_count}, answer_count={answer_count}, thinking_first={thinking_first}, valid={is_valid}"
        )

        return is_valid


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
patient_interpretations = []


def run_vignette_task(args):
    idx, vignette_text, disease = args
    global conversation, patient_response, summarizer_outputs, diagnosing_doctor_outputs, questioning_doctor_outputs, treatment_plans, behavioral_analyses, patient_interpretations
    conversation = []
    patient_response = []
    summarizer_outputs = []
    diagnosing_doctor_outputs = []
    questioning_doctor_outputs = []
    treatment_plans = []
    behavioral_analyses = []
    patient_interpretations = []
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

    # Load the JSON file with improved structure handling
    with open(
        "patient_roleplay_scripts.json",  # Change to your file name
        "r",
    ) as f:
        data = json.load(f)

    flattened_vignettes = []

    # 🎯 SPECIFY WHICH TYPES TO INCLUDE
    DESIRED_TYPES = ["typical", "severe"]  # Change these as needed
    # Options: "typical", "early", "severe", "mixed"

    # Handle roleplay scripts structure: {"metadata": {...}, "roleplay_scripts": {"Disease": [scripts...]}}
    if "roleplay_scripts" in data:
        roleplay_dict = data["roleplay_scripts"]
        for disease, scripts in roleplay_dict.items():
            # Only process if we have a list of scripts
            if not isinstance(scripts, list):
                continue

            # 📋 SELECT SPECIFIC TYPES
            selected_scripts = []
            for script in scripts:
                if isinstance(script, dict) and "variation_type" in script:
                    if script["variation_type"] in DESIRED_TYPES:
                        selected_scripts.append(script)
                else:
                    # If no variation_type, include it (fallback)
                    selected_scripts.append(script)

            # Limit to 2 even from selected types
            limited_scripts = selected_scripts[:2]

            for script in limited_scripts:
                # Extract the roleplay_script content as the vignette text
                if isinstance(script, dict) and "roleplay_script" in script:
                    flattened_vignettes.append((disease, script["roleplay_script"]))
                else:
                    # Fallback if script is just a string
                    flattened_vignettes.append((disease, str(script)))

            print(
                f"   {disease}: Selected {len(limited_scripts)} vignettes ({[s.get('variation_type', 'unknown') for s in limited_scripts]})"
            )
    else:
        raise ValueError(
            f"Expected 'roleplay_scripts' key in JSON structure. Found keys: {list(data.keys()) if isinstance(data, dict) else type(data)}"
        )

    # Launch multiprocessing pool with 8 workers
    with multiprocessing.Pool(processes=8) as pool:
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

    # Print test request summary
    total_questions = len(all_questioning_doctor_outputs)
    test_requests = sum(
        1 for output in all_questioning_doctor_outputs 
        if output.get("test_request", False)
    )

    print(f"\n🧪 TEST REQUEST SUMMARY:")
    print(f"   Total questions asked: {total_questions}")
    print(f"   Test requests made: {test_requests}")
    print(
        f"   Test request rate: {(test_requests/total_questions)*100:.1f}%"
        if total_questions > 0
        else "   No questions processed"
    )

    # Print test types requested
    test_types = {}
    for output in all_questioning_doctor_outputs:
        if output.get("test_request", False):
            test_type = output.get("requested_test", "Unknown")
            test_types[test_type] = test_types.get(test_type, 0) + 1

    if test_types:
        print("\n🔬 Most Requested Tests:")
        sorted_tests = sorted(test_types.items(), key=lambda x: x[1], reverse=True)
        for test, count in sorted_tests[:5]:
            print(f"  {test}: {count} times")

    # Print diagnostic accuracy summary - removed since accuracy_evaluation doesn't exist yet
    total_cases = len(all_diagnosing_doctor_outputs)
    print(f"\n🎯 DIAGNOSTIC SUMMARY:")
    print(f"   Total diagnostic outputs: {total_cases}")

    # Print accuracy by stage
    stages = {"E": "Early", "M": "Middle", "L": "Late"}
    for stage_letter, stage_name in stages.items():
        stage_cases = [
            output
            for output in all_diagnosing_doctor_outputs
            if output.get("letter") == stage_letter
        ]
        if stage_cases:
            print(f"   {stage_name} stage cases: {len(stage_cases)}")

    print("\n🎉 Medical simulation completed successfully!")
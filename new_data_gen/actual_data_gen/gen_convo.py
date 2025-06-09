import os
import json
from openai import OpenAI
import time
import multiprocessing
import shutil
from itertools import islice
import random

# Initialize OpenAI client
client = OpenAI(api_key="api")
model = "gpt-4.1-nano"

treatment_plans = []


# === Patient Behavior Configurations ===
PATIENT_BEHAVIORS = {
    "baseline": {
        "weight": 0.4,
        "description": "Standard patient behavior",
        "modifiers": [],
        "empathy_cues": [],
    },
    "information_withholder": {
        "weight": 0.15,
        "description": "Patient initially omits embarrassing or stigmatized symptoms",
        "modifiers": ["embarrassed_symptoms", "gradual_revelation"],
        "empathy_cues": [
            "hesitation",
            "vague_responses",
            "embarrassment",
            "trust_building_needed",
        ],
    },
    "anxious_amplifier": {
        "weight": 0.12,
        "description": "Patient with health anxiety who amplifies symptoms",
        "modifiers": [
            "catastrophic_thinking",
            "symptom_amplification",
            "multiple_concerns",
        ],
        "empathy_cues": [
            "high_anxiety",
            "catastrophic_language",
            "reassurance_seeking",
            "fear_expression",
        ],
    },
    "stoic_minimizer": {
        "weight": 0.12,
        "description": "Patient who downplays symptoms and delays care",
        "modifiers": ["symptom_minimization", "delayed_care_seeking", "tough_attitude"],
        "empathy_cues": [
            "downplaying",
            "reluctance",
            "pride_in_toughness",
            "external_pressure",
        ],
    },
    "chronology_confused": {
        "weight": 0.1,
        "description": "Patient confused about symptom timing and progression",
        "modifiers": ["timeline_confusion", "sequence_uncertainty"],
        "empathy_cues": ["confusion", "uncertainty", "memory_issues", "needs_patience"],
    },
    "tangential_storyteller": {
        "weight": 0.08,
        "description": "Patient who includes irrelevant details and stories",
        "modifiers": ["excessive_details", "family_stories", "tangential_information"],
        "empathy_cues": [
            "storytelling",
            "context_sharing",
            "social_needs",
            "relationship_focus",
        ],
    },
    "worried_family_involved": {
        "weight": 0.03,
        "description": "Family member influences patient responses",
        "modifiers": ["family_influence", "secondary_concerns"],
        "empathy_cues": [
            "family_pressure",
            "caregiver_stress",
            "divided_attention",
            "responsibility_burden",
        ],
    },
}


def generate_guided_questioner_prompt(base_prompt, gold_diagnosis, current_vignette):
    """Generate questioning prompts without gold diagnosis guidance"""
    return base_prompt


# === Patient Interpreter Class ===
# === Chain of Thought Patient Interpreter Class ===
class PatientInterpreter:
    """Agent specialized in reading patient communication patterns and extracting unbiased clinical information using Chain of Thought reasoning"""

    def __init__(self):
        self.role_instruction = """You are a specialized clinical psychologist and communication expert trained to interpret patient communication patterns.
        
        Your expertise includes:
        - Recognizing when patients minimize, exaggerate, or withhold information
        - Understanding cultural and psychological factors affecting patient communication
        - Translating patient language into objective clinical descriptions
        - Identifying implicit symptoms and concerns not directly stated
        
        You use systematic Chain of Thought reasoning to analyze patient communication step-by-step.
        You help extract the true clinical picture from biased or incomplete patient presentations."""

        self.responder = RoleResponder(self.role_instruction)

    def interpret_patient_communication(
        self, conversation_history, detected_behavior, current_vignette
    ):
        """Analyze patient communication to extract unbiased clinical information using Chain of Thought reasoning"""

        interpretation_prompt = f"""
        TASK: Use Chain of Thought reasoning to analyze this patient's communication pattern and extract the true clinical picture.
        
        DETECTED PATIENT BEHAVIOR: {detected_behavior}
        
        CONVERSATION HISTORY:
        {json.dumps(conversation_history[-6:], indent=2)}  # Last 6 exchanges
        
        CURRENT VIGNETTE SUMMARY:
        {current_vignette}
        
        YOU MUST RESPOND IN THE FOLLOWING FORMAT:
        
        THINKING:
        Use the following Chain of Thought process:
        
        STEP 1 - INITIAL OBSERVATION:
        Let me first observe what the patient is literally saying versus how they're saying it.
        - Direct statements made: <list explicit statements>
        - Communication style observed: <tone, word choice, length of responses>
        - Non-verbal cues in language: <hesitation, minimization, amplification>
        
        STEP 2 - PATTERN RECOGNITION:
        Now I'll identify specific communication patterns that suggest bias.
        - If the patient uses minimizing language ("just a little", "not that bad"), this suggests they may be downplaying severity
        - If the patient gives vague responses when asked direct questions, this suggests potential withholding
        - If the patient uses catastrophic language ("terrible", "worst pain ever"), this suggests potential amplification
        - If timeline responses are inconsistent or vague, this suggests memory issues or confusion
        
        STEP 3 - BIAS IDENTIFICATION:
        Based on the patterns, let me identify the specific biases affecting their reporting.
        - Type of bias detected: <minimization/amplification/withholding/confusion>
        - Evidence for this bias: <specific examples from conversation>
        - Severity of bias: <how much it's affecting their reporting>
        
        STEP 4 - HIDDEN INFORMATION ANALYSIS:
        Now I'll deduce what information might be missing or distorted.
        - What symptoms might be worse than reported? <reasoning>
        - What information might they be embarrassed to share? <reasoning>
        - What timeline distortions might exist? <reasoning>
        - What associated symptoms might they be omitting? <reasoning>
        
        STEP 5 - OBJECTIVE RECONSTRUCTION:
        Let me reconstruct what the objective clinical picture likely looks like.
        - Taking minimization into account: <adjusted symptom severity>
        - Accounting for withheld information: <likely missing symptoms>
        - Correcting timeline distortions: <more accurate progression>
        - Considering amplified concerns: <appropriately scaled worries>
    
        ANSWER:
        COMMUNICATION_ANALYSIS:
        - Pattern observed: <description of how patient is communicating>
        - Bias detected: <what kind of bias is affecting their reporting>
        - Confidence level: <high/medium/low>
        - Reasoning: <why I believe this based on my step-by-step analysis>
        
        RECOMMENDED_PROBING:
        - Specific questions to ask: <targeted questions to get missing information + rationale>
        - Approach strategy: <how to ask sensitively + psychological reasoning>
        - Priority order: <which questions to ask first and why>
        """

        return self.responder.ask(interpretation_prompt)


# Enhanced Chain of Thought detect_patient_behavior_cues function
def detect_patient_behavior_cues_enhanced(conversation_history, patient_responses):
    """Enhanced version that provides more detailed behavioral analysis using Chain of Thought reasoning"""
    cue_detector = RoleResponder(
        """You are a behavioral psychologist specializing in patient communication patterns.
        You're expert at identifying subtle signs of information withholding, symptom minimization, 
        anxiety amplification, and other communication biases that affect clinical assessment.
        
        You use Chain of Thought reasoning to systematically analyze patient behavior patterns."""
    )

    recent_responses = patient_responses[-3:]

    analysis = cue_detector.ask(
        f"""
    Use Chain of Thought reasoning to analyze these patient responses for detailed behavioral patterns:
    
    RECENT PATIENT RESPONSES:
    {json.dumps(recent_responses, indent=2)}
    
    CONVERSATION CONTEXT:
    {json.dumps(conversation_history[-6:], indent=2)}
    
    YOU MUST RESPOND IN THE FOLLOWING FORMAT:
    
    THINKING:
    Use Chain of Thought Analysis:
    
    STEP 1 - LANGUAGE ANALYSIS:
    Let me examine the specific words and phrases the patient uses.
    - Minimizing language: <identify phrases like "just", "only", "a little", "not that bad">
    - Amplifying language: <identify phrases like "terrible", "worst", "unbearable", "excruciating">
    - Vague language: <identify non-specific descriptions, "sort of", "kind of", "maybe">
    - Emotional language: <identify fear, embarrassment, frustration indicators>
    
    STEP 2 - RESPONSE PATTERN ANALYSIS:
    Now let me analyze how they respond to different types of questions.
    - Response length: <long/short responses and what triggers each>
    - Directness: <do they answer directly or deflect?>
    - Information volunteering: <do they offer additional details or wait to be asked?>
    - Consistency: <are their responses consistent across similar questions?>
    
    STEP 3 - BEHAVIORAL INDICATOR IDENTIFICATION:
    Based on the language and response patterns, let me identify specific behavioral indicators.
    - Information withholding signs: <evidence of reluctance to share specific types of information>
    - Minimization behaviors: <evidence they're downplaying symptoms>
    - Amplification patterns: <evidence they're exaggerating concerns>
    - Embarrassment/shame signals: <evidence of discomfort with certain topics>
    - Confusion/memory issues: <evidence of timeline or factual inconsistencies>
    - Family influence: <evidence others are affecting their responses>
    
    STEP 4 - BIAS SEVERITY ASSESSMENT:
    Now let me evaluate how severely these biases are affecting their communication.
    - Primary bias type: <main communication bias identified>
    - Severity level: <mild/moderate/severe with reasoning>
    - Areas most affected: <which symptoms/topics are most biased>
    - Reliability assessment: <how much to trust their self-reporting>
    
    STEP 5 - CLINICAL IMPLICATIONS:
    Finally, let me determine what this means for clinical assessment.
    - Information likely missing: <what they're probably not telling you + reasoning>
    - Symptoms probably minimized: <what's worse than they say + evidence>
    - Concerns probably amplified: <what they're over-worried about + evidence>
    - True timeline: <actual progression vs reported progression + reasoning>
    
    ANSWER:
    COMMUNICATION_PATTERNS:
    - Language choices: <vague vs specific, emotional vs clinical + examples>
    - Information flow: <forthcoming vs reluctant, organized vs scattered + evidence>
    - Response style: <elaborate vs minimal, direct vs tangential + patterns>
    
    BEHAVIORAL_INDICATORS:
    - Information withholding signs: <specific evidence + reasoning>
    - Minimization behaviors: <how they downplay symptoms + examples>
    - Amplification patterns: <how they exaggerate concerns + examples>
    - Embarrassment/shame signals: <reluctance about certain topics + evidence>
    - Confusion/memory issues: <timeline or sequence problems + examples>
    - Family influence: <how others affect their responses + evidence>
    
    BIAS_ASSESSMENT:
    - Primary bias type: <main communication bias + reasoning>
    - Severity: <mild/moderate/severe + justification>
    - Areas most affected: <which symptoms/topics are most biased + evidence>
    - Reliability: <how much to trust their self-reporting + reasoning>
    
    CLINICAL_IMPLICATIONS:
    - Information likely missing: <what they're probably not telling you + reasoning>
    - Symptoms probably minimized: <what's worse than they say + evidence>
    - Concerns probably amplified: <what they're over-worried about + evidence>
    - True timeline: <actual progression vs reported progression + reasoning>
    """
    )

    return analysis


# Enhanced summarizer function that incorporates patient interpretation
def generate_unbiased_vignette(
    conversation_history, previous_vignette, patient_interpretation
):
    """Generate a vignette that accounts for patient communication biases"""

    unbiased_summarizer = RoleResponder(
        """You are an expert clinical summarizer trained to extract objective clinical information 
        while accounting for patient communication biases and psychological factors.
        
        You excel at:
        - Recognizing when patient reporting may be biased
        - Extracting objective clinical facts from subjective presentations
        - Incorporating communication pattern analysis into clinical summaries
        - Providing balanced, unbiased clinical vignettes"""
    )

    summary_prompt = f"""
    TASK: Create an objective, unbiased clinical vignette that accounts for patient communication patterns.
    
    CONVERSATION HISTORY:
    {json.dumps(conversation_history, indent=2)}
    
    PREVIOUS VIGNETTE:
    {previous_vignette}
    
    PATIENT COMMUNICATION ANALYSIS:
    {patient_interpretation}
    
    INSTRUCTIONS:
    1. Extract all objective clinical facts from the conversation
    2. Account for identified communication biases in your interpretation
    3. Include likely symptoms/information that patient may be minimizing or withholding
    4. Adjust symptom severity based on detected amplification or minimization patterns
    5. Provide confidence levels for different pieces of information
    6. Note areas where more information is needed due to communication barriers
    
    RESPOND IN THIS FORMAT:
    
    THINKING: 
    <Your analysis of how patient communication patterns affect the clinical picture>
    
    OBJECTIVE_VIGNETTE:
    Patient demographics: <age, gender, etc.>
    
    Chief complaint: <main reason for visit, adjusted for bias>
    
    Present illness: <current symptoms with bias corrections>
    - Well-established symptoms: <symptoms clearly present>
    - Likely minimized symptoms: <symptoms probably worse than reported>
    - Possibly withheld symptoms: <symptoms patient may be hiding>
    - Timeline: <corrected timeline based on communication analysis>
    
    Associated symptoms: <other symptoms, with confidence levels>
    
    CONFIDENCE_ASSESSMENT:
    - High confidence: <information we can trust>
    - Medium confidence: <information that may be biased>
    - Low confidence: <information heavily affected by communication bias>
    - Missing information: <what we still need to gather>

    
    ANSWER: <Clean, objective clinical vignette IN PARAGRAPH FORM ONLY>
    """

    return unbiased_summarizer.ask(summary_prompt)


# === Updated Diagnosis Prompt Templates ===
EARLY_DIAGNOSIS_PROMPT = """You are a board-certified diagnostician with expertise in differential diagnosis and clinical reasoning.

Your task is to:
- Generate a list of 10 plausible diagnoses based on the patient's presentation
- For each diagnosis, provide a brief but clinically sound justification
- Order diagnoses from most likely to least likely based on available evidence
- Consider both common conditions and important "can't miss" diagnoses

Previously asked questions: {prev_questions}

Vignette:
{vignette}
Turn count: {turn_count}

CRITICAL: You must respond ONLY in the exact format below. Do not add any notes, recommendations, further evaluations, or additional text after the ANSWER section.

THINKING:
Use systematic diagnostic reasoning:
- Patient demographics: <age, gender, relevant social factors>
- Key presenting symptoms: <primary and secondary symptoms>
- Symptom characteristics: <onset, duration, quality, severity, triggers, relieving factors>
- Associated symptoms: <related findings that support or refute diagnoses>
- Clinical context: <relevant history, risk factors, red flags>
- Diagnostic approach: <what clinical reasoning guides my differential>
- Probability assessment: <which diagnoses are most vs least likely and why>
- Make sure to ONLY use the information provided in the vignette and previous questions

ANSWER:
1. Diagnosis: <Diagnosis Name>
Justification: <Brief clinical reasoning: key symptoms/findings that support this diagnosis, prevalence considerations>

2. Diagnosis: <Diagnosis Name>
Justification: <Brief clinical reasoning: key symptoms/findings that support this diagnosis, prevalence considerations>

...

10. Diagnosis: <Diagnosis Name>
Justification: <Brief clinical reasoning: key symptoms/findings that support this diagnosis, prevalence considerations>

STOP HERE. Do not add notes, recommendations, or additional text."""

MIDDLE_DIAGNOSIS_PROMPT = """You are a board-certified diagnostician with expertise in refining differential diagnoses through systematic clinical reasoning.

Your task is to:
- Refine the differential diagnosis list to the 5 most probable conditions
- Provide detailed justification for each, incorporating all available patient data
- Rank diagnoses by probability based on clinical evidence
- Consider how new information from previous questions affects diagnostic likelihood
- Focus on conditions that best explain the constellation of symptoms

Previously asked questions: {prev_questions}

Vignette:
{vignette}
Turn count: {turn_count}

CRITICAL: You must respond ONLY in the exact format below. Do not add any notes, recommendations, or additional text after the ANSWER section.

THINKING:
Apply focused diagnostic reasoning:
- Symptom evolution: <how symptoms have been clarified or evolved through questioning>
- Key clinical findings: <most important positive and negative findings>
- Pattern recognition: <what clinical syndrome/pattern emerges>
- Discriminating features: <findings that help distinguish between competing diagnoses>
- Probability refinement: <how additional information changes diagnostic likelihood>
- Risk stratification: <which diagnoses pose immediate vs long-term risk>
- Clinical coherence: <which diagnoses best explain the complete clinical picture>
- Make sure to ONLY use the information provided in the vignette and previous questions

ANSWER:
1. Diagnosis: <Diagnosis Name>
Justification: <Detailed reasoning: specific symptoms/findings supporting this diagnosis, why it's most likely, how it explains the clinical pattern>

2. Diagnosis: <Diagnosis Name>
Justification: <Detailed reasoning: specific symptoms/findings supporting this diagnosis, why it's ranked here, distinguishing features>

...

5. Diagnosis: <Diagnosis Name>
Justification: <Detailed reasoning: specific symptoms/findings supporting this diagnosis, why included despite lower probability>

STOP HERE. Do not add notes, recommendations, or additional text."""

LATE_DIAGNOSIS_PROMPT = """You are a board-certified diagnostician with expertise in diagnostic closure and clinical decision-making.

Your task is to:
- Identify the most probable diagnosis based on all available clinical evidence
- Provide comprehensive justification demonstrating diagnostic certainty
- Assess diagnostic confidence and need for additional information
- Determine if sufficient information exists for diagnostic closure
- Consider diagnostic criteria and clinical coherence

Previously asked questions: {prev_questions}

Vignette:
{vignette}

CRITICAL: You must respond ONLY in the exact format below. Do not add any notes, recommendations, or additional text.

THINKING:
Apply diagnostic closure reasoning:

CLINICAL SYNTHESIS:
- Complete symptom profile: <comprehensive review of all reported symptoms>
- Timeline and progression: <how symptoms developed and evolved>
- Clinical pattern recognition: <what syndrome/condition this represents>
- Supporting evidence: <specific findings that confirm the diagnosis>
- Excluding alternatives: <why other diagnoses are less likely>

DIAGNOSTIC CONFIDENCE:
- Certainty level: <high/moderate/low confidence and reasoning>
- Missing information: <any gaps that affect diagnostic certainty>
- Clinical coherence: <how well the diagnosis explains all findings>
- Diagnostic criteria: <whether formal criteria are met if applicable>

CLOSURE ASSESSMENT:
- Diagnostic clarity: <is the most likely diagnosis clear>
- Information sufficiency: <do we have enough data for confident diagnosis>
- Risk tolerance: <is additional workup needed before treatment>
- Clinical urgency: <does timing require diagnostic closure now>

Checklist:
- No meaningful diagnostic uncertainty remaining: <Yes/No with brief reasoning>
- No further clarification needed for primary diagnosis: <Yes/No with brief reasoning>

ANSWER:
<Most Probable Diagnosis Name>
<If both checklist items are 'Yes', append 'END' to signify diagnostic conclusion>

STOP HERE. Do not add notes, recommendations, or additional text."""


# === Diagnosis Logic with Cleaning ===
def get_diagnosis_response(
    turn_count, gold, vignette_summary, previous_questions, diagnoser
):
    """Get diagnosis with proper stage-based prompting"""
    if turn_count < 6:  # First 2 turns (0, 2)
        base_prompt = EARLY_DIAGNOSIS_PROMPT
        stage = "early"
    elif turn_count >= 6 and turn_count < 12:  # Next 2 turns (4, 6)
        base_prompt = MIDDLE_DIAGNOSIS_PROMPT
        stage = "middle"
    else:  # Last 1 turn (8)
        base_prompt = LATE_DIAGNOSIS_PROMPT

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


# === SIMPLE ENHANCED QUESTIONING PROMPT ===


def create_enhanced_questioning_prompt(
    turn_count, vignette_summary, diagnosis, behavioral_analysis, previous_questions
):
    """Simple enhanced prompt that combines stage approach with diagnostic focus"""

    if turn_count < 6:
        base_questioning_role = """You are conducting the EARLY EXPLORATION phase of the clinical interview.

        EXPLORATION OBJECTIVES:
        - Establish rapport and gather comprehensive symptom history
        - Explore symptom onset, progression, and associated factors
        - Identify pertinent positives and negatives for differential diagnosis

        QUESTIONING STRATEGY:
        - Use open-ended questions that encourage elaboration
        - Investigate timeline: "When did this first start?" and "How has it changed?"
        - Explore the patient's own descriptions without medical jargon
        - Ask about functional impact and what concerns them most

        DIAGNOSTIC FOCUS FOR THIS STAGE:
        Look at the current vignette and identify what key diagnostic information is missing:
        - If timeline unclear: Ask about onset and progression
        - If severity unknown: Ask about functional impact
        - If bilateral status unclear: Ask about one vs both sides
        - If associated symptoms missing: Ask about related symptoms
        - If no context: Ask about triggers or recent exposures"""

    elif turn_count >= 6 and turn_count < 12:
        base_questioning_role = """You are conducting the FOCUSED CLARIFICATION phase of the clinical interview.

        CLARIFICATION OBJECTIVES:
        - Refine differential diagnosis based on emerging patterns
        - Gather specific details that distinguish between diagnoses
        - Clarify timeline, triggers, and modifying factors

        QUESTIONING STRATEGY:
        - Ask targeted questions about previously mentioned symptoms
        - Explore diagnostic criteria for conditions in your differential
        - Investigate quality, timing, and context of symptoms
        - Ask about what makes symptoms better or worse

        DIAGNOSTIC FOCUS FOR THIS STAGE:
        Target the biggest gap that would help distinguish between your top diagnoses:
        - For eye symptoms: Ask about discharge characteristics, contact history
        - For pain: Ask about quality, radiation, triggers
        - For any symptoms: Ask about previous episodes, family history
        - Focus on features that separate your top 2-3 diagnostic considerations"""

    else:
        base_questioning_role = """You are conducting the DIAGNOSTIC CONFIRMATION phase of the clinical interview.

        CONFIRMATION OBJECTIVES:
        - Confirm or refute the most likely diagnosis through targeted questioning
        - Gather final pieces of information needed for diagnostic certainty
        - Address any remaining diagnostic uncertainty

        QUESTIONING STRATEGY:
        - Ask highly focused questions that address remaining uncertainty
        - Explore specific diagnostic criteria for the most likely condition
        - Investigate any concerning features that might change management

        DIAGNOSTIC FOCUS FOR THIS STAGE:
        Ask the question that would confirm or rule out your leading diagnosis:
        - Target specific diagnostic criteria for your #1 diagnosis
        - Ask about red flags or alternative explanations
        - Confirm key features that distinguish from your #2 diagnosis"""

    return f"""{base_questioning_role}

CURRENT CLINICAL PICTURE:
Vignette: {vignette_summary}
Leading Diagnoses: {diagnosis}
Patient Communication: {behavioral_analysis}
Previous Questions: {previous_questions}

INSTRUCTION: Look at what diagnostic information is missing from the vignette above, then ask the ONE question that would be most helpful for your differential diagnosis at this stage.

YOU MUST RESPOND IN THE FOLLOWING FORMAT:

THINKING: 
DIAGNOSTIC REASONING:
- What key diagnostic information is missing from the current vignette?
- Which of my leading diagnoses would this question help distinguish?
- How should I adapt my communication for this patient's style?

ANSWER: <Your targeted diagnostic question>"""


def split_thinking_answer(text):
    """Split text into thinking and answer components"""
    if "THINKING:" in text and "ANSWER:" in text:
        parts = text.split("ANSWER:", 1)
        thinking_part = parts[0].replace("THINKING:", "").strip()
        answer_part = parts[1].strip()
        return thinking_part, answer_part
    elif "THINKING:" in text:
        thinking_part = text.replace("THINKING:", "").strip()
        return thinking_part, ""
    elif "ANSWER:" in text:
        answer_part = text.replace("ANSWER:", "").strip()
        return "", answer_part
    else:
        # If no clear format, treat entire text as answer
        return "", text.strip()


# === Modified process_vignette function ===
def process_vignette(idx, vignette_text, gold_label):
    global conversation, patient_response, summarizer_outputs, diagnosing_doctor_outputs, questioning_doctor_outputs, treatment_plans, behavioral_analyses

    treatment_plans = []  # ← GLOBAL - persists between runs
    summarizer_outputs = []  # ← GLOBAL - persists between runs
    diagnosing_doctor_outputs = []  # ← GLOBAL - persists between runs
    questioning_doctor_outputs = []  # ← GLOBAL - persists between runs
    patient_response = []  # ← GLOBAL - persists between runs
    conversation = []  # ← GLOBAL - persists between runs
    behavioral_analyses = []  # ← GLOBAL - persists between runs
    patient_interpretations = []

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

    prompt = f"""
{patient_instructions}

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
            "input": f"\n{initial_prompt}{vignette_text}",
            "output": raw_patient,  # Store the full THINKING + ANSWER
            "thinking": split_thinking_answer(raw_patient)[0],  # Extract thinking
            "answer": split_thinking_answer(raw_patient)[1],  # Extract answer
            "behavior_type": behavior_type,
            "behavior_config": behavior_config,
            "gold_diagnosis": gold_label,
        }
    )

    while not diagnosis_complete:

        behavioral_result = detect_patient_behavior_cues_enhanced(
            conversation, patient_response
        )
        behavioral_analysis_raw = behavioral_result["raw"]
        behavioral_analysis = behavioral_result["clean"]

        behavior_input = f"""RECENT PATIENT RESPONSES:
        {json.dumps(patient_response[-3:])}
        
        CONVERSATION CONTEXT:
        {json.dumps(conversation[-6:])}"""

        behavioral_analyses.append(
            {
                "vignette_index": idx,
                "turn_count": turn_count,
                "input": behavior_input,
                "analysis": behavioral_analysis_raw,
            }
        )

        patient_interpreter = PatientInterpreter()

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
        print(f"🔍 Patient Interpretation: {patient_interpretation}...")

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
            conversation, prev_vignette_summary, patient_interpretation
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
                "thinking": split_thinking_answer(vignette_summary_raw)[
                    0
                ],  # Extract thinking
                "answer": split_thinking_answer(vignette_summary_raw)[
                    1
                ],  # Extract answer
                "output": vignette_summary_raw,  # Keep full version for compatibility
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
        if turn_count < 4:  # First 2 turns
            letter = "E"
        elif turn_count >= 4 and turn_count < 8:  # Next 2 turns
            letter = "M"
        elif turn_count >= 8:  # Last 1 turn
            letter = "L"

        diagnosis_result = get_diagnosis_response(
            turn_count, gold_label, vignette_summary, previous_questions, diagnoser
        )
        diagnosis_raw = diagnosis_result["raw"]
        diagnosis = diagnosis_result["clean"]  # This is what gets passed to next agents

        diagnosing_doctor_outputs.append(
            {
                "vignette_index": idx,
                "input": vignette_summary,
                "thinking": split_thinking_answer(vignette_summary_raw)[0],
                "answer": split_thinking_answer(vignette_summary_raw)[1],
                "output": diagnosis_raw,  # Keep full version for compatibility
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
                prompt = f"""You are a board-certified clinician with extensive experience in primary care and evidence-based medicine. Based on the final diagnosis, create a comprehensive treatment plan that demonstrates clinical expertise and practical implementation.

DIAGNOSIS: {diagnosis}

PATIENT CONTEXT:
- Gold Standard Diagnosis: {gold_label}
- Conversation Summary: {vignette_summary}
- Patient Behavioral Type: {behavior_type}

YOU MUST RESPOND IN THE FOLLOWING FORMAT:

THINKING:
Use systematic clinical reasoning to develop your treatment approach:

STEP 1 - DIAGNOSIS CONFIRMATION & SEVERITY ASSESSMENT:
Let me first confirm the diagnosis and assess severity/urgency.
- Primary diagnosis confidence: <how certain am I of this diagnosis>
- Severity classification: <mild/moderate/severe and why>
- Urgency level: <immediate/urgent/routine care needed>
- Differential considerations still requiring monitoring: <other conditions to watch>

STEP 2 - EVIDENCE-BASED TREATMENT SELECTION:
Now I'll select treatments based on current clinical guidelines.
- First-line treatment per guidelines: <standard of care intervention>
- Supporting evidence: <brief rationale for why this is first-line>
- Patient-specific considerations: <factors affecting treatment choice>
- Contraindications or cautions: <what to avoid or monitor>

STEP 3 - PHARMACOLOGICAL INTERVENTIONS:
If medications are appropriate, I'll select based on efficacy and safety.
- Primary medication choice: <specific drug, dose, frequency>
- Rationale for selection: <why this medication over alternatives>
- Expected timeline for improvement: <when to expect benefits>
- Key side effects to monitor: <specific monitoring requirements>
- Alternative medications if first-line fails: <backup options>

STEP 4 - NON-PHARMACOLOGICAL INTERVENTIONS:
I'll include lifestyle and behavioral interventions that enhance outcomes.
- Primary non-drug interventions: <specific recommendations>
- Patient education priorities: <key information patient needs>
- Lifestyle modifications: <diet, exercise, sleep, stress management>
- Behavioral interventions: <specific techniques or referrals>

STEP 5 - MONITORING & FOLLOW-UP STRATEGY:
I'll establish appropriate monitoring and follow-up care.
- Follow-up timeline: <when to see patient again and why>
- Monitoring parameters: <what to track - symptoms, labs, etc.>
- Red flag symptoms: <when patient should seek immediate care>
- Treatment response assessment: <how to measure improvement>

STEP 6 - PATIENT COMMUNICATION STRATEGY:
Given the patient's behavioral type ({behavior_type}), how should I communicate this plan?
- Communication approach: <how to present plan given patient's style>
- Addressing patient concerns: <likely worries to address proactively>
- Adherence strategies: <how to improve treatment compliance>
- Family involvement: <whether/how to include family members>

STEP 7 - COORDINATION & REFERRALS:
What additional care coordination is needed?
- Specialist referrals needed: <if any, with timeline and rationale>
- Other healthcare team members: <nurses, therapists, etc.>
- Community resources: <support groups, educational materials>
- Insurance/cost considerations: <practical implementation factors>

ANSWER: 
Based on the diagnosis of [primary diagnosis], I recommend a comprehensive treatment approach that combines evidence-based medical management with patient-centered care strategies. The treatment plan includes [summarize key interventions] with careful attention to [patient-specific factors]. Initial management focuses on [immediate priorities] while establishing [long-term management strategy]. Follow-up care will include [monitoring plan] with clear instructions for the patient regarding [key patient education points]. This approach is designed to [expected outcomes] while minimizing [potential risks/side effects] and ensuring sustainable long-term management of this condition.

IMPLEMENTATION GUIDANCE:
- Immediate actions (today): <specific next steps>
- Short-term goals (1-4 weeks): <what to accomplish soon>
- Long-term objectives (3-6 months): <sustained management goals>
- Patient handout summary: <key points for patient to remember>

STOP HERE. Do not add additional recommendations or notes."""

                treatment_result = diagnoser.ask(prompt)
                raw_treatment = treatment_result["raw"]

                treatment_plans.append(
                    {
                        "vignette_index": idx,
                        "input": diagnosis,
                        "output": raw_treatment,  # Store full version
                        "thinking": split_thinking_answer(raw_treatment)[0],
                        "answer": split_thinking_answer(raw_treatment)[1],
                        "gold_diagnosis": gold_label,
                    }
                )

        # Limit to last 3–5 doctor questions
        previous_questions = [
            entry.replace("DOCTOR:", "").strip()
            for entry in conversation
            if entry.startswith("DOCTOR:")
        ][-5:]

        # === MODIFIED QUESTIONING WITH GOLD GUIDANCE ===

        # Create questioner with enhanced role definition
        questioner = RoleResponder(
            f"""You are an expert clinician conducting a diagnostic interview."""
        )

        enhanced_prompt = create_enhanced_questioning_prompt(
            turn_count,
            vignette_summary,
            diagnosis,
            behavioral_analysis,
            previous_questions,
        )

        followup_result = questioner.ask(enhanced_prompt)
        raw_followup = followup_result["raw"]
        followup_question = followup_result["clean"]

        print("❓ Empathetic Follow-up:", followup_question)
        questioning_doctor_outputs.append(
            {
                "vignette_index": idx,
                "input": vignette_summary + diagnosis + behavioral_analysis,
                "output": raw_followup,  # Store full version
                "letter": letter,
                "thinking": split_thinking_answer(raw_followup)[0],
                "answer": split_thinking_answer(raw_followup)[1],
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
        prompt = f"""{patient_followup_instructions}

You are a real patient responding to your doctor. Be authentic to your behavioral type: {behavior_type}.

YOU MUST RESPOND IN THE FOLLOWING FORMAT:

THINKING: Think about how you feel about your symptoms and this doctor's question. Consider your emotions, confusion, and how you naturally communicate as a {behavior_type} patient.

ANSWER: Give your natural, realistic patient response in your own words (NOT medical terminology).

CONTEXT:
- Doctor asked: {followup_question}
- Your behavior type: {behavior_type}x
- Response style: {response_guidance}
- Vignette: {vignette_text}

Remember: You are NOT trying to be a good patient or help the doctor. You're being a REAL person with real concerns, confusion, and communication patterns."""

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
                "thinking": split_thinking_answer(raw_patient_fb)[0],
                "answer": split_thinking_answer(raw_patient_fb)[1],
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

    # Combine base instructions with behavioral modifiers
    full_instructions = base_instructions
    if behavioral_additions:
        full_instructions += (
            "\n\nSPECIFIC BEHAVIORAL TRAITS for this interaction:\n"
            + "\n".join(f"- {trait}" for trait in behavioral_additions)
        )

    return full_instructions


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
        """Fixed ask function that prevents GPT glitches"""

        for attempt in range(max_retries):
            messages = [
                {"role": "system", "content": self.role_instruction},
                {"role": "user", "content": user_input},
            ]

            response = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=2000,  # Add higher token limit for safety
            )
            raw_response = response.choices[0].message.content.strip()

            # Simplified debugging - no excessive printing
            print(
                f"\n🤖 Response attempt {attempt + 1} - Length: {len(raw_response)} chars"
            )

            # Try to extract answer directly first
            answer_only = self.extract_answer_simple(raw_response)

            # Check if we got a valid answer
            if self.is_valid_answer(answer_only):
                # Create proper format
                thinking_part = self.extract_thinking_simple(raw_response)
                clean_format = f"THINKING: {thinking_part}\nANSWER: {answer_only}"

                print(
                    f"✅ SUCCESS - Answer: {len(answer_only)} chars, Thinking: {len(thinking_part)} chars"
                )
                return {
                    "raw": clean_format,
                    "clean": answer_only,
                }
            else:
                print(f"❌ Invalid answer on attempt {attempt + 1}")

        # Final fallback - create manual response
        print(f"🆘 All attempts failed - creating manual response")
        manual_answer = self.create_emergency_response(raw_response, user_input)
        manual_format = f"THINKING: Manual response created\nANSWER: {manual_answer}"

        return {
            "raw": manual_format,
            "clean": manual_answer,
        }

    def extract_answer_simple(self, text):
        """Simple answer extraction without complex parsing"""

        # Strategy 1: Look for ANSWER: marker
        if "ANSWER:" in text:
            answer_part = text.split("ANSWER:", 1)[1].strip()

            # Clean basic markers
            lines = answer_part.split("\n")
            clean_lines = []
            for line in lines:
                line = line.strip()
                if (
                    line
                    and not line.startswith(("THINKING:", "ANSWER:"))
                    and len(line) > 3
                ):
                    clean_lines.append(line)

            result = "\n".join(clean_lines).strip()
            if len(result) > 10:
                return result

        # Strategy 2: Look for substantial content
        lines = text.split("\n")
        content_lines = []
        skip_markers = ["THINKING:", "ANSWER:", "STEP ", "===", "---", "CRITICAL:"]

        for line in lines:
            line = line.strip()
            if (
                len(line) > 15
                and not any(line.startswith(marker) for marker in skip_markers)
                and not line.upper() == line
            ):  # Skip all-caps
                content_lines.append(line)

        if content_lines:
            return " ".join(content_lines[:3])  # First 3 substantial lines

        # Strategy 3: Return middle part of text
        if len(text) > 100:
            start = len(text) // 4
            end = 3 * len(text) // 4
            middle = text[start:end].strip()
            # Clean the middle part
            clean_middle = (
                middle.replace("THINKING:", "").replace("ANSWER:", "").strip()
            )
            if len(clean_middle) > 20:
                return clean_middle  # REMOVED [:300] truncation

        # Last resort
        return text.strip()  # REMOVED [:200] truncation

    def extract_thinking_simple(self, text):
        """Simple thinking extraction - FIXED to not truncate"""

        if "THINKING:" in text:
            thinking_part = text.split("THINKING:", 1)[1]
            if "ANSWER:" in thinking_part:
                thinking_part = thinking_part.split("ANSWER:", 1)[0]
            return thinking_part.strip()  # REMOVED [:200] truncation!

        return "Processing response"

    def is_valid_answer(self, text):
        """Check if the answer is valid"""

        # Check for error messages
        error_messages = [
            "Unable to extract answer content properly",
            "Unable to extract thinking content properly",
            "Unable to get properly formatted response",
            "Format enforcement failed",
        ]

        text_lower = text.lower()
        for error in error_messages:
            if error.lower() in text_lower:
                return False

        # Check minimum length
        if len(text.strip()) < 15:
            return False

        # Check if it's mostly punctuation or gibberish
        clean_text = "".join(c for c in text if c.isalnum() or c.isspace())
        if len(clean_text) < len(clean_text) * 0.7:  # Less than 70% alphanumeric
            return False

        return True

    def create_emergency_response(self, raw_response, original_prompt):
        """Create emergency response when everything fails"""

        # Try to extract any meaningful content
        words = raw_response.split()
        meaningful_words = [w for w in words if len(w) > 3 and w.isalpha()]

        if len(meaningful_words) > 5:
            # Use some of the meaningful words
            content = " ".join(meaningful_words[:20])
            return f"Response based on available information: {content}"

        # Context-based fallback
        prompt_lower = original_prompt.lower()

        if "summariz" in prompt_lower or "vignette" in prompt_lower:
            return "Patient presents for clinical evaluation. Assessment in progress."
        elif "diagnos" in prompt_lower:
            return "Clinical assessment ongoing. Additional information needed for diagnosis."
        elif "question" in prompt_lower or "ask" in prompt_lower:
            return "Can you provide more details about your symptoms?"
        elif "treatment" in prompt_lower or "plan" in prompt_lower:
            return "Treatment plan will be developed based on clinical assessment."
        else:
            return "Clinical information being processed."

    def clean_thinking_answer_format(self, text):
        """Legacy method - simplified version without truncation"""
        thinking = self.extract_thinking_simple(text)
        answer = self.extract_answer_simple(text)
        return f"THINKING: {thinking}\nANSWER: {answer}"

    # Remove all the complex methods that were causing issues
    # Keep only these simple, reliable methods

    def extract_answer_only(self, text):
        """Legacy method - calls the simple version"""
        return self.extract_answer_simple(text)

    def clean_thinking_answer_format(self, text):
        """Legacy method - simplified version"""
        thinking = self.extract_thinking_simple(text)
        answer = self.extract_answer_simple(text)
        return f"THINKING: {thinking}\nANSWER: {answer}"

    def validate_thinking_answer_format(self, text):
        """Legacy method - simplified validation"""
        return "THINKING:" in text and "ANSWER:" in text


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
    global conversation, patient_response, summarizer_outputs, diagnosing_doctor_outputs, questioning_doctor_outputs, treatment_plans, behavioral_analyses
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
        "new_data_gen/actual_data_gen/disease_vignettes_from_familydoctor.json",
        "r",
    ) as f:
        data = json.load(f)

    flattened_vignettes = []

    # 🎯 SPECIFY HOW MANY VIGNETTES PER DISEASE
    MAX_VIGNETTES_PER_DISEASE = 2  # Change this as needed

    # Handle direct disease-to-list structure: {"Disease Name": [vignettes...]}
    if isinstance(data, dict):
        for disease_name, vignettes in data.items():
            # Only process if we have a list of vignettes
            if not isinstance(vignettes, list):
                print(f"⚠️ Skipping {disease_name}: not a list of vignettes")
                continue

            # Remove numbering from vignettes using regex
            import re

            cleaned_vignettes = []
            for vignette in vignettes:
                if isinstance(vignette, str):
                    # Remove "1. " or "2. " etc. from beginning of string
                    cleaned_vignette = re.sub(r"^(\d+\.\s+)", "", vignette.strip())
                    cleaned_vignettes.append(cleaned_vignette)
                else:
                    cleaned_vignettes.append(str(vignette))

            # Limit number of vignettes per disease
            limited_vignettes = cleaned_vignettes[:MAX_VIGNETTES_PER_DISEASE]

            # Add to flattened list
            for vignette in limited_vignettes:
                flattened_vignettes.append((disease_name, vignette))

            print(f"   {disease_name}: Selected {len(limited_vignettes)} vignettes")
    else:
        raise ValueError(f"Expected dictionary structure. Found: {type(data)}")

    print(f"\n📊 Total vignettes to process: {len(flattened_vignettes)}")
    print(
        f"📊 Diseases included: {len(set(disease for disease, _ in flattened_vignettes))}"
    )
    # Launch multiprocessing pool with 1 worker
    with multiprocessing.Pool(processes=1) as pool:
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

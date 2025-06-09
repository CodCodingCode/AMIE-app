import os
import json
import hashlib
import pickle
from openai import OpenAI
import time
import multiprocessing
import shutil
from itertools import islice
import random

# Initialize OpenAI client
client = OpenAI(
    api_key=""
)
model = "gpt-4.1-nano"

treatment_plans = []


class OpenAICache:
    def __init__(self, cache_dir="openai_cache"):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        self.hits = 0
        self.misses = 0

    def _get_cache_key(self, messages, model, max_tokens=None):
        """Generate a unique cache key for the request"""
        # Create a hash of the request parameters
        cache_data = {"messages": messages, "model": model, "max_tokens": max_tokens}
        cache_string = json.dumps(cache_data, sort_keys=True)
        return hashlib.md5(cache_string.encode()).hexdigest()

    def _get_cache_path(self, cache_key):
        """Get the file path for a cache key"""
        return os.path.join(self.cache_dir, f"{cache_key}.pkl")

    def get(self, messages, model, max_tokens=None):
        """Try to get a cached response"""
        cache_key = self._get_cache_key(messages, model, max_tokens)
        cache_path = self._get_cache_path(cache_key)

        if os.path.exists(cache_path):
            try:
                with open(cache_path, "rb") as f:
                    cached_response = pickle.load(f)
                self.hits += 1
                print(f"💾 Cache HIT - Key: {cache_key[:8]}...")
                return cached_response
            except Exception as e:
                print(f"⚠️ Cache read error: {e}")
                # If cache read fails, continue to make API call

        self.misses += 1
        return None

    def set(self, messages, model, response, max_tokens=None):
        """Cache a response"""
        cache_key = self._get_cache_key(messages, model, max_tokens)
        cache_path = self._get_cache_path(cache_key)

        try:
            with open(cache_path, "wb") as f:
                pickle.dump(response, f)
            print(f"💾 Cache SAVE - Key: {cache_key[:8]}...")
        except Exception as e:
            print(f"⚠️ Cache write error: {e}")

    def stats(self):
        """Get cache statistics"""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0
        return {
            "hits": self.hits,
            "misses": self.misses,
            "total": total,
            "hit_rate": hit_rate,
        }

    def clear(self):
        """Clear all cache files"""
        if os.path.exists(self.cache_dir):
            shutil.rmtree(self.cache_dir)
            os.makedirs(self.cache_dir, exist_ok=True)
        self.hits = 0
        self.misses = 0
        print("🗑️ Cache cleared")


# Global cache instance
openai_cache = OpenAICache()


def cached_openai_call(messages, model, max_tokens=4000):
    """Make an OpenAI API call with caching"""

    # Try to get from cache first
    cached_response = openai_cache.get(messages, model, max_tokens)
    if cached_response is not None:
        return cached_response

    # Make API call if not in cache
    try:
        response = client.chat.completions.create(
            model=model, messages=messages, max_tokens=max_tokens
        )

        # Cache the response
        openai_cache.set(messages, model, response, max_tokens)

        return response

    except Exception as e:
        print(f"❌ OpenAI API Error: {e}")
        raise


# === SIMPLE DIAGNOSIS PROMPT TEMPLATES ===
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


# === Diagnosis Logic ===
def get_diagnosis_response(
    turn_count, gold, vignette_summary, previous_questions, diagnoser
):
    """Get diagnosis with proper stage-based prompting"""
    if turn_count < 6:  # First 2 turns
        base_prompt = EARLY_DIAGNOSIS_PROMPT
        stage = "early"
    elif turn_count >= 6 and turn_count < 12:  # Next 2 turns
        base_prompt = MIDDLE_DIAGNOSIS_PROMPT
        stage = "middle"
    else:  # Last 1 turn
        base_prompt = LATE_DIAGNOSIS_PROMPT

    response = diagnoser.ask(
        base_prompt.format(
            prev_questions=json.dumps(previous_questions),
            vignette=vignette_summary,
            turn_count=turn_count,
        )
    )

    return response


# === SIMPLE QUESTIONING PROMPT ===
def create_simple_questioning_prompt(
    turn_count, vignette_summary, diagnosis, previous_questions
):
    """Simple questioning prompt based on stage"""

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
Previous Questions: {previous_questions}

INSTRUCTION: Look at what diagnostic information is missing from the vignette above, then ask the ONE question that would be most helpful for your differential diagnosis at this stage.

YOU MUST RESPOND IN THE FOLLOWING FORMAT:

THINKING: 
DIAGNOSTIC REASONING:
- What key diagnostic information is missing from the current vignette?
- Which of my leading diagnoses would this question help distinguish?

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
        return "", text.strip()


# === Simple process_vignette function ===
def process_vignette(idx, vignette_text, gold_label):
    global conversation, patient_response, summarizer_outputs, diagnosing_doctor_outputs, questioning_doctor_outputs, treatment_plans

    treatment_plans = []
    summarizer_outputs = []
    diagnosing_doctor_outputs = []
    questioning_doctor_outputs = []
    patient_response = []
    conversation = []

    print(f"🎯 Gold diagnosis: {gold_label}")

    previous_questions = []
    initial_prompt = "What brings you in today?"
    conversation.clear()
    conversation.append(f"DOCTOR: {initial_prompt}")

    # Create simple patient with basic instructions
    patient = RoleResponder(
        """You are simulating a real patient in conversation with their doctor. 
Respond naturally and realistically, as if you are experiencing symptoms yourself — but like a real patient, you are NOT medically trained and do NOT understand what's important or what anything means. 
You have NOT spoken to any other doctors. 
You may feel scared, unsure, or even embarrassed. 
You are NOT trying to impress the doctor with a clear answer — just describe what you feel in your own confused way."""
    )

    # Simple patient prompt
    prompt = f"""
You are generating training data for a reasoning model that will simulate patient responses. 

Your task is to create a THINKING section that shows what a patient reasoning model should consider, and an ANSWER section with the actual patient response.

THINKING should include:
- How the patient feels about their symptoms
- What the patient understands (or doesn't understand) about their condition
- The patient's emotional state and concerns
- How the patient decides what to share and what language to use
- The patient's reasoning about symptom severity and timing

Patient background: {vignette_text}
Doctor's question: {initial_prompt}

YOU MUST mention age and biological gender in the first sentence of the ANSWER.

YOU MUST RESPOND IN THE FOLLOWING FORMAT:

THINKING: I need to think about how this patient would process their symptoms and decide what to tell the doctor. The patient would be considering [their symptoms], feeling [emotional state], and trying to explain [specific concerns] in their own non-medical language. They would be uncertain about [medical aspects] but clear about [personal experience]. The patient should sound [characteristics] and focus on [main concerns].

ANSWER: [The actual patient response in natural, non-medical language]"""

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
            "output": raw_patient,
            "thinking": split_thinking_answer(raw_patient)[0],
            "answer": split_thinking_answer(raw_patient)[1],
            "gold_diagnosis": gold_label,
        }
    )

    while not diagnosis_complete:
        # Simple summarizer without behavioral analysis
        summarizer2_input = f"CONVERSATION HISTORY:\n{json.dumps(conversation, indent=2)}\n\nPREVIOUS VIGNETTE:\n{prev_vignette_summary}"
        summarizer_input = f"""You are generating training data for a clinical summarizer reasoning model.

Create a THINKING section that shows how a summarizer reasoning model should analyze a conversation and extract clinical information.

THINKING should include:
- How to identify key clinical information from patient language
- How to distinguish between relevant and irrelevant details
- How to organize symptoms chronologically and by system
- How to translate patient language into clinical terminology
- How to assess completeness of information

CONVERSATION HISTORY:
{conversation}

PREVIOUS VIGNETTE:
{prev_vignette_summary}

YOU MUST RESPOND IN THE FOLLOWING FORMAT:

THINKING: The summarizer model should analyze this conversation by first identifying [key symptoms mentioned], then organizing them by [systematic approach]. It should translate [patient language] into [clinical terms] while noting [timeline/progression]. The model should recognize [important details] and identify [missing information]. The summary should be [structured approach] focusing on [clinical priorities].

ANSWER: [Clean, structured clinical vignette in paragraph form]"""

        vignette_result = summarizer.ask(summarizer_input)
        vignette_summary_raw = vignette_result["raw"]
        vignette_summary = vignette_result["clean"]

        summarizer_outputs.append(
            {
                "vignette_index": idx,
                "input": summarizer2_input,
                "thinking": split_thinking_answer(vignette_summary_raw)[0],
                "answer": split_thinking_answer(vignette_summary_raw)[1],
                "output": vignette_summary_raw,
                "turn_count": turn_count,
                "gold_diagnosis": gold_label,
            }
        )

        prev_vignette_summary = vignette_summary

        if "ANSWER:" in vignette_summary:
            vignette_summary = vignette_summary.split("ANSWER:")[1].strip()

        # Diagnosis
        print("Turn count:", turn_count)
        letter = ""
        if turn_count < 4:
            letter = "E"
        elif turn_count >= 4 and turn_count < 8:
            letter = "M"
        elif turn_count >= 8:
            letter = "L"

        diagnosis_result = get_diagnosis_response(
            turn_count, gold_label, vignette_summary, previous_questions, diagnoser
        )
        diagnosis_raw = diagnosis_result["raw"]
        diagnosis = diagnosis_result["clean"]

        diagnosing_doctor_outputs.append(
            {
                "vignette_index": idx,
                "input": vignette_summary,
                "thinking": split_thinking_answer(diagnosis_raw)[0],
                "answer": split_thinking_answer(diagnosis_raw)[1],
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
                print(f"✅ Reached END for vignette {idx}. Moving to next.\n")

                # Simple treatment generation
                treatment_input = {
                    "final_diagnosis": diagnosis,
                    "vignette_summary": vignette_summary,
                    "patient_context": {
                        "gold_diagnosis": gold_label,
                        "conversation_summary": (
                            conversation[-6:] if len(conversation) > 6 else conversation
                        ),
                    },
                }

                prompt = f"""You are generating training data for a treatment planning reasoning model.

Create a THINKING section showing how a treatment reasoning model should develop comprehensive treatment plans with specific clinical reasoning.

FINAL DIAGNOSIS: {diagnosis}

CLINICAL VIGNETTE SUMMARY: {vignette_summary}

PATIENT CONTEXT:
- Gold Standard Diagnosis: {gold_label}
- Recent Conversation: {conversation[-6:] if len(conversation) > 6 else conversation}

YOU MUST RESPOND IN THE FOLLOWING FORMAT:

THINKING: 
The treatment reasoning model should approach this case systematically:

STEP 1 - DIAGNOSIS CONFIRMATION & SEVERITY ASSESSMENT:
The model should confirm this is [specific diagnosis] based on [specific symptoms from vignette]. It should assess severity as [mild/moderate/severe] because [specific evidence]. The urgency level should be [immediate/urgent/routine] due to [specific clinical indicators]. The model should consider differential diagnoses that still need monitoring: [specific alternatives].

STEP 2 - EVIDENCE-BASED TREATMENT SELECTION:
The model should select [specific first-line treatment] as the primary intervention based on [specific guideline/evidence]. It should consider patient-specific factors including [age, comorbidities, severity] that modify treatment choice. Key contraindications to consider are [specific contraindications] and cautions include [specific monitoring needs].

STEP 3 - PHARMACOLOGICAL INTERVENTIONS:
The model should select [specific medication] at [specific dose and frequency] because [specific rationale]. Expected timeline for improvement is [specific timeframe] with [specific endpoints]. Key side effects to monitor include [specific adverse effects] requiring [specific monitoring]. Alternative medications if first-line fails include [specific backup options with rationale].

STEP 4 - NON-PHARMACOLOGICAL INTERVENTIONS:
The model should recommend [specific non-drug interventions] because [evidence-based rationale]. Patient education should focus on [specific teaching points] relevant to this condition. Lifestyle modifications should include [specific changes] with [specific timelines]. Behavioral interventions should address [specific patient needs].

STEP 5 - MONITORING & FOLLOW-UP STRATEGY:
The model should schedule follow-up in [specific timeframe] to assess [specific parameters]. Monitoring should include [specific tests/assessments] at [specific intervals]. Red flag symptoms requiring immediate care are [specific warning signs]. Treatment response should be measured by [specific criteria].

STEP 6 - PATIENT COMMUNICATION STRATEGY:
The model should communicate using [specific approach] because the patient [specific characteristics from conversation]. It should address likely concerns about [specific worries] and use [specific strategies] to improve adherence. Family involvement should be [specific recommendations].

STEP 7 - COORDINATION & REFERRALS:
The model should refer to [specific specialists] within [specific timeframe] for [specific reasons]. Other healthcare team members needed include [specific roles]. Community resources should include [specific programs]. Cost/insurance considerations include [specific factors].

ANSWER: 
IMMEDIATE ACTIONS (Today):
• [Specific medication] [dose] [route] [frequency]
• [Specific diagnostic test/imaging] within [timeframe]
• [Specific monitoring parameter] every [interval]
• [Specific patient instruction]

SHORT-TERM MANAGEMENT (1-4 weeks):
• Follow-up appointment in [specific days] to assess [specific outcomes]
• [Specific medication adjustments] based on [specific criteria]
• [Specific lifestyle modifications] with [specific targets]
• [Specific referrals] if [specific conditions met]

LONG-TERM CARE (3-6 months):
• [Specific monitoring schedule] with [specific tests]
• [Specific prevention strategies] to prevent [specific complications]
• [Specific patient education] about [specific topics]
• [Specific care coordination] between [specific providers]

PATIENT EDUCATION PRIORITIES:
• [Specific warning signs] that require immediate medical attention
• [Specific medication instructions] including [specific details]
• [Specific lifestyle changes] with [specific goals]
• [Specific follow-up instructions] and [specific contact information]"""

                treatment_result = diagnoser.ask(prompt)
                raw_treatment = treatment_result["raw"]

                treatment_plans.append(
                    {
                        "vignette_index": idx,
                        "input": f"""DIAGNOSIS: {diagnosis} VIGNETTE: {vignette_summary} """,  # Clean input string
                        "output": raw_treatment,  # Full THINKING + ANSWER
                        "thinking": split_thinking_answer(raw_treatment)[
                            0
                        ],  # Extracted thinking
                        "answer": split_thinking_answer(raw_treatment)[
                            1
                        ],  # Extracted answer
                        "gold_diagnosis": gold_label,
                        "turn_count": turn_count,
                    }
                )

        # Limit to last 3–5 doctor questions
        previous_questions = [
            entry.replace("DOCTOR:", "").strip()
            for entry in conversation
            if entry.startswith("DOCTOR:")
        ][-5:]

        # Simple questioning
        questioner = RoleResponder(
            f"""You are an expert clinician conducting a diagnostic interview."""
        )

        simple_prompt = create_simple_questioning_prompt(
            turn_count,
            vignette_summary,
            diagnosis,
            previous_questions,
        )

        followup_result = questioner.ask(simple_prompt)
        raw_followup = followup_result["raw"]
        followup_question = followup_result["clean"]

        print("❓ Follow-up:", followup_question)
        questioning_doctor_outputs.append(
            {
                "vignette_index": idx,
                "input": vignette_summary + diagnosis,
                "output": raw_followup,
                "letter": letter,
                "thinking": split_thinking_answer(raw_followup)[0],
                "answer": split_thinking_answer(raw_followup)[1],
                "gold_diagnosis": gold_label,
            }
        )
        conversation.append(f"DOCTOR: {followup_question}")

        # Simple patient response
        prompt = f"""
        
        
        You are generating training data for a patient reasoning model.

Create a THINKING section showing how a patient reasoning model should process the doctor's question and decide how to respond.

THINKING should include:
- How the patient interprets the doctor's question
- What memories or sensations the patient recalls
- The patient's emotional reaction to the question
- How the patient decides what information is relevant
- The patient's reasoning about how to express their experience

CONTEXT:
- Doctor asked: {followup_question}
- Patient background: {vignette_text}

YOU MUST RESPOND IN THE FOLLOWING FORMAT:

THINKING: The patient model should consider how this question makes the patient think about [specific aspect]. The patient would recall [memories/sensations] and feel [emotional response]. They would reason that [relevance assessment] and decide to mention [specific details] while being uncertain about [medical implications]. The response should sound [natural characteristics].

ANSWER: [Natural patient response]"""

        patient_fb_result = patient.ask(prompt)
        raw_patient_fb = patient_fb_result["raw"]
        patient_followup_text = patient_fb_result["clean"]

        print("🗣️ Patient:", patient_followup_text)
        conversation.append(f"PATIENT: {patient_followup_text}")
        patient_response.append(
            {
                "vignette_index": idx,
                "input": vignette_text + followup_question,
                "output": raw_patient_fb,
                "thinking": split_thinking_answer(raw_patient_fb)[0],
                "answer": split_thinking_answer(raw_patient_fb)[1],
                "turn_count": turn_count,
                "gold_diagnosis": gold_label,
            }
        )

        turn_count += 2

    # Save results
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
        "gold_diagnosis": gold_label,
    }


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

            response = cached_openai_call(messages, model, max_tokens=4000)
            raw_response = response.choices[0].message.content.strip()

            print(
                f"\n🤖 Response attempt {attempt + 1} - Length: {len(raw_response)} chars"
            )

            answer_only = self.extract_answer_simple(raw_response)

            if self.is_valid_answer(answer_only):
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

        print(f"🆘 All attempts failed - creating manual response")
        manual_answer = self.create_emergency_response(raw_response, user_input)
        manual_format = f"THINKING: Manual response created\nANSWER: {manual_answer}"

        return {
            "raw": manual_format,
            "clean": manual_answer,
        }

    def extract_answer_simple(self, text):
        if "ANSWER:" in text:
            answer_part = text.split("ANSWER:", 1)[1].strip()
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

        lines = text.split("\n")
        content_lines = []
        skip_markers = ["THINKING:", "ANSWER:", "STEP ", "===", "---", "CRITICAL:"]

        for line in lines:
            line = line.strip()
            if (
                len(line) > 15
                and not any(line.startswith(marker) for marker in skip_markers)
                and not line.upper() == line
            ):
                content_lines.append(line)

        if content_lines:
            return " ".join(content_lines[:3])

        if len(text) > 100:
            start = len(text) // 4
            end = 3 * len(text) // 4
            middle = text[start:end].strip()
            clean_middle = (
                middle.replace("THINKING:", "").replace("ANSWER:", "").strip()
            )
            if len(clean_middle) > 20:
                return clean_middle

        return text.strip()

    def extract_thinking_simple(self, text):
        if "THINKING:" in text:
            thinking_part = text.split("THINKING:", 1)[1]
            if "ANSWER:" in thinking_part:
                thinking_part = thinking_part.split("ANSWER:", 1)[0]
            return thinking_part.strip()  # Removed truncation

        return "Processing response"

    def is_valid_answer(self, text):
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

        if len(text.strip()) < 15:
            return False

        clean_text = "".join(c for c in text if c.isalnum() or c.isspace())
        if len(clean_text) < len(text) * 0.7:
            return False

        return True

    def create_emergency_response(self, raw_response, original_prompt):
        words = raw_response.split()
        meaningful_words = [w for w in words if len(w) > 3 and w.isalpha()]

        if len(meaningful_words) > 5:
            content = " ".join(meaningful_words[:20])
            return f"Response based on available information: {content}"

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


# === Use the Class for Roles ===
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

    # Load the JSON file
    with open(
        "new_data_gen/actual_data_gen/disease_vignettes_from_familydoctor.json",
        "r",
    ) as f:
        data = json.load(f)

    flattened_vignettes = []

    # 🎯 SPECIFY HOW MANY VIGNETTES PER DISEASE
    MAX_VIGNETTES_PER_DISEASE = 2

    # Handle direct disease-to-list structure: {"Disease Name": [vignettes...]}
    if isinstance(data, dict):
        import re

        for disease_name, vignettes in data.items():
            if not isinstance(vignettes, list):
                print(f"⚠️ Skipping {disease_name}: not a list of vignettes")
                continue

            # Remove numbering from vignettes
            cleaned_vignettes = []
            for vignette in vignettes:
                if isinstance(vignette, str):
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

    # Launch multiprocessing pool workers
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

    # Print diagnostic accuracy summary
    total_cases = len(all_diagnosing_doctor_outputs)
    print(f"\n🎯 DIAGNOSTIC SUMMARY:")
    print(f"   Total cases processed: {total_cases}")

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

    print(
        f"\n✅ Processing complete! Generated {len(flattened_vignettes)} clinical conversations."
    )

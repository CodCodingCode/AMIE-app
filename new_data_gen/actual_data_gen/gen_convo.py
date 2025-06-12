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
    api_key="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"
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
Conversation: {conversation}

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
- Prioritize life threatening conditions first, then work down to less emergent diagnoses.

Example THINKING:
THINKING:
I need to analyze this clinical presentation systematically to generate a differential diagnosis list.

Starting with the key clinical features:
- 72-year-old male (elderly, higher risk demographics)
- Sudden onset abdominal and back pain 
- Pain quality: sharp and constant
- Associated dizziness and lightheadedness
- No nausea, vomiting, chest pain, or shortness of breath mentioned

The combination of sudden onset abdominal/back pain in an elderly male immediately raises red flags for vascular emergencies. The word "sudden" is crucial - this suggests an acute catastrophic event rather than gradual onset.

The dizziness and lightheadedness are particularly concerning when paired with sudden abdominal pain. This could indicate hemodynamic compromise, suggesting internal bleeding or shock.

Let me think through the most likely diagnoses:

1. Abdominal Aortic Aneurysm (AAA) Rupture - This fits perfectly. Elderly male, sudden severe abdominal/back pain, and signs of hemodynamic compromise (dizziness/lightheadedness suggesting hypotension). AAA rupture classically presents with abdominal pain radiating to the back.

2. Aortic Dissection - Could present with sudden severe pain, though typically more chest/back pain. The hemodynamic instability fits.

3. Perforated Peptic Ulcer - Sudden onset severe abdominal pain, but usually presents with more peritoneal signs and less back pain.

4. Pancreatitis - Can cause severe abdominal pain radiating to back, but usually more gradual onset and associated with nausea/vomiting (which are absent here).

5. Renal Colic/Nephrolithiasis - Can cause severe flank/back pain, but usually more colicky and less likely to cause hemodynamic compromise.

Given the demographics (elderly male), the sudden onset, the specific pain pattern (abdominal AND back), and the hemodynamic symptoms (dizziness/lightheadedness), AAA rupture should be at the top of my differential.

The absence of chest pain makes MI less likely, though it should still be considered in this demographic. The absence of nausea/vomiting makes GI causes somewhat less likely but doesn't rule them out.

I need to prioritize life-threatening conditions first, then work down to less emergent diagnoses.


ANSWER:
1. Diagnosis: <Diagnosis Name>
2. Diagnosis: <Diagnosis Name>
...
10. Diagnosis: <Diagnosis Name>

STOP HERE. Do not add notes, recommendations, or additional text."""

MIDDLE_DIAGNOSIS_PROMPT = """You are a board-certified diagnostician with expertise in refining differential diagnoses through systematic clinical reasoning.

Your task is to:
- Refine the differential diagnosis list to the 5 most probable conditions
- Provide detailed justification for each, incorporating all available patient data
- Rank diagnoses by probability based on clinical evidence
- Consider how new information from previous questions affects diagnostic likelihood
- Focus on conditions that best explain the constellation of symptoms

Previously asked questions: {prev_questions}
Conversation: {conversation}

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
- Prioritize life threatening conditions first, then work down to less emergent diagnoses.


ANSWER:
1. Diagnosis: <Diagnosis Name>
2. Diagnosis: <Diagnosis Name>
...
10. Diagnosis: <Diagnosis Name>
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
Conversation: {conversation}

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
1. Diagnosis: <Diagnosis Name>
2. Diagnosis: <Diagnosis Name>
3. Diagnosis: <Diagnosis Name>
4. Diagnosis: <Diagnosis Name>
5. Diagnosis: <Diagnosis Name>
END

STOP HERE. Do not add notes, recommendations, or additional text."""


# === Diagnosis Logic ===
def get_diagnosis_response(
    turn_count, gold, vignette_summary, previous_questions, diagnoser, conversation
):
    """Get diagnosis with proper stage-based prompting"""
    if turn_count < 6:  # First 2 turns
        base_prompt = EARLY_DIAGNOSIS_PROMPT
        stage = "early"
    elif turn_count >= 6 and turn_count < 14:  # Next 2 turns
        base_prompt = MIDDLE_DIAGNOSIS_PROMPT
        stage = "middle"
    else:  # Last 1 turn
        base_prompt = LATE_DIAGNOSIS_PROMPT

    response = diagnoser.ask(
        base_prompt.format(
            prev_questions=json.dumps(previous_questions),
            vignette=vignette_summary,
            conversation=json.dumps(conversation),
            turn_count=turn_count,
        )
    )

    return response


def clean_patient_input(vignette_text, doctor_question):
    """Clean and format the patient input properly"""

    # Extract just the vignette text without the doctor question mixed in
    if "What brings you in today?" in vignette_text:
        # Split and take only the vignette part
        parts = vignette_text.split("What brings you in today?")
        if len(parts) > 1:
            clean_vignette = parts[1].strip()
        else:
            clean_vignette = vignette_text.strip()
    else:
        clean_vignette = vignette_text.strip()

    return clean_vignette


# Updated prompt generation:
def generate_patient_prompt(vignette_text, doctor_question, conversation):

    # Clean the vignette text
    clean_vignette = clean_patient_input(vignette_text, doctor_question)

    prompt = f"""
You are generating training data for a patient reasoning model that simulates how THIS SPECIFIC patient would think and respond.

Create a THINKING section showing how a patient reasoning model should process this particular patient's situation and decide how to communicate with the doctor.

PATIENT CLINICAL BACKGROUND:
{clean_vignette}

DOCTOR'S QUESTION: 
{doctor_question}

CONVERSATION:
{json.dumps(conversation)}

YOU MUST mention age and biological gender in the first sentence of the ANSWER.

YOU MUST RESPOND IN THE FOLLOWING FORMAT:

THINKING: 
Please EXPLAIN how this patient would respond the doctors question. SOURCE THE VIGNETTE. SOURCE THE QUESTION. SOURCE THE CONVERSATION. 

PATIENT-SPECIFIC CONTEXT:
This [age] [gender] patient with [relevant medical history] would approach this situation influenced by [age-related concerns], [medical history impact], and [demographic factors]. Given their [specific background], they would be particularly worried about [specific fears].

SYMPTOM PROCESSING & LANGUAGE CHOICE:
The patient would experience [specific symptoms] and struggle to articulate [particular sensations]. They would choose words like "[patient's likely language]" because [reasoning for word choice]. The [specific symptom characteristic] would be most alarming because [patient's perspective].

EMOTIONAL & PSYCHOLOGICAL STATE:
Given the [symptom severity/type] and their [age/background], the patient would feel [specific emotions]. They would be thinking "[internal monologue]" and worried specifically about [age-appropriate concerns like mortality, family, independence].

COMMUNICATION STRATEGY:
This patient would decide to share [specific information] while withholding [specific concerns] because [reasoning]. They would use [communication style] language because [generational/personal factors]. They would emphasize [what they think is most important] to convey [their main concern].

MEDICAL UNDERSTANDING & MISCONCEPTIONS:
The patient would (not) understand [specific medical aspects] and might think [potential misconceptions]. They would be uncertain about [medical significance] but clear about [personal experience]. They might connect this to [previous health experiences or family history].

ANSWER: I am a [AGE] [GENDER]. [Natural patient response that reflects the specific reasoning above, using age-appropriate language and concerns. RESPOND WITH 1-2 SENTENCES ONLY, FOCUSING ON WHAT THE PATIENT WOULD SAY IN RESPONSE TO THE DOCTOR'S QUESTION. DO NOT ADD ANYTHING ELSE. DO NOT USE MEDICAL TERMINOLOGY OR JARGON. DO NOT EXPLAIN YOUR REASONING HERE. JUST RESPOND AS THE PATIENT WOULD.]"""

    return prompt


# === SIMPLE QUESTIONING PROMPT ===
def create_simple_questioning_prompt(
    turn_count, vignette_summary, diagnosis, previous_questions, conversation
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

    elif turn_count >= 6 and turn_count < 14:
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
        - MAKE SURE YOU GET MORE INFORMATION. ASK QUESTIONS THAT WOULD GET YOU MORE INFORMATION IN THE FOLLOWING TOPICS IN ORDER TO HAVE A BETTER DIAGNOSIS: Time, severity, context, onset, location, duration, family history, medical history, social history, etc.

        DIAGNOSTIC FOCUS FOR THIS STAGE:
        Target the biggest gap that would help distinguish between your top diagnoses:
        EXAMPLE:
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
        - Confirm key features that distinguish from your #2 diagnosis
        USING THE LEADING DIAGNOSES, PLEASE ASK QUESTIONS THAT TAILOR TOWARDS FINDING WHICH DISEASE OF THE ONES IN THE DIFFERENTIAL DIAGNOSES IS THE MOST LIKELY DIAGNOSIS. Ask eliminating questions that would help you confirm or rule out the most likely diagnosis.
        """

    return f"""{base_questioning_role}

CURRENT CLINICAL PICTURE:
Vignette: {vignette_summary}
Leading Diagnoses: {diagnosis}
Previous Questions: {previous_questions}
Conversation: {json.dumps(conversation)}

INSTRUCTION: Look at what diagnostic information is missing from the vignette above, then ask the ONE question that would be most helpful for your differential diagnosis at this stage. PLEASE DO NOT ASK PREVIOUSLY ASKED QUESTIONS. 

YOU MUST RESPOND IN THE FOLLOWING FORMAT:

THINKING: 
THIS IS A MUST: Based on the vignette and previous questions, EXPLAIN WHY YOU ARE ASKING A SPECIFIC QUESTION. Be SPECIFIC about each fact. Source the Diagnoses, source the Vignette, and source the Previous Questions. 
Consider:
- What key diagnostic information is missing from the current vignette?
- What key diagnostic information is in the current vignette?
- Which of my leading diagnoses would this question help distinguish?
- What is the most important piece of information I need to gather at this stage?

ANSWER: <Your targeted diagnostic question - DO NOT REPEAT PREVIOUS QUESTIONS.>"""


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
    # With this clean version:
    clean_prompt = generate_patient_prompt(vignette_text, initial_prompt, conversation)
    patient_result = patient.ask(clean_prompt)

    turn_count = 0
    diagnosis_complete = False
    prev_vignette_summary = ""

    raw_patient = patient_result["raw"]
    patient_response_text = patient_result["clean"]

    print("🗣️ Patient's Reply:", patient_response_text)
    conversation.append(f"PATIENT: {patient_response_text}")
    patient_response.append(
        {
            "vignette_index": idx,
            "input": f"VIGNETTE: {vignette_text} QUESTION: {initial_prompt}",
            "output": raw_patient,
            "thinking": split_thinking_answer(raw_patient)[0],
            "answer": split_thinking_answer(raw_patient)[1],
            "gold_diagnosis": gold_label,
        }
    )

    while not diagnosis_complete:
        # Simple summarizer without behavioral analysis
        summarizer2_input = f"CONVERSATION: {json.dumps(conversation)} PREVIOUS VIGNETTE:\n{prev_vignette_summary}"
        summarizer_input = f"""You are generating training data for a clinical summarizer reasoning model.

Create a THINKING section that shows how a summarizer reasoning model should extract and organize ONLY the facts stated in THIS SPECIFIC conversation without adding interpretations or diagnoses.

CONVERSATION HISTORY:
{conversation}

PREVIOUS VIGNETTE:
{prev_vignette_summary}

YOU MUST RESPOND IN THE FOLLOWING FORMAT:
THINKING: 
Explain how you would extract and organize the clinical information from the conversation and how that supports the ANSWER's you will give. PLEASE SOURCE CONVERSATION HISTORY, PLEASE SOURCE PREVIOUS VIGNETTES MAKE SURE IT IS DETAILED. Focus on:   

STEP 1 - FACT EXTRACTION:
The model should identify exactly what the patient stated: "[exact patient words]" and extract only the explicitly mentioned facts: [list only stated facts]. It should NOT infer, assume, or add any information not directly stated by the patient.

STEP 2 - TERMINOLOGY TRANSLATION:
The model should translate the patient's lay language into clinical terminology while staying faithful to what was said: "[patient's words]" becomes "[clinical equivalent]" without adding severity, implications, or interpretations.

STEP 3 - CHRONOLOGICAL ORGANIZATION:
The model should organize the timeline based only on what the patient reported: [onset timing], [progression], [current status] - using only the patient's stated information about timing and sequence.

STEP 4 - SYSTEMATIC ORGANIZATION:
The model should categorize the reported symptoms by system: [symptom category] - [exactly what patient said], without inferring additional symptoms or clinical significance.

STEP 5 - COMPLETENESS ASSESSMENT:
The model should identify what information is missing by noting: [specific gaps in history] that were not addressed in the conversation, without suggesting what those gaps might contain.

ANSWER: 
IN PARAGRAPH FORM THAT INCLUDES THE FOLLOWING INFORMATION:
Chief Complaint: [Exactly what the patient said brought them in]
Demographics: [Only age, gender, and facts explicitly stated]  
History of Present Illness: [Chronological facts as reported by patient, translated to clinical terms]
Associated Symptoms: [Only symptoms explicitly mentioned by patient]
Pertinent Negatives: [Only denials explicitly stated by patient]
Missing Information: [What wasn't discussed, without speculation about content Add family information, social history, time, context, progression, duration, etc.]"""

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
        if turn_count < 6:
            letter = "E"
        elif turn_count >= 6 and turn_count < 14:
            letter = "M"
        elif turn_count >= 14:
            letter = "L"

        diagnosis_result = get_diagnosis_response(
            turn_count,
            gold_label,
            vignette_summary,
            previous_questions,
            diagnoser,
            json.dumps(conversation),
        )
        diagnosis_raw = diagnosis_result["raw"]
        diagnosis = diagnosis_result["clean"]

        diagnosing_doctor_outputs.append(
            {
                "vignette_index": idx,
                "input": f"VIGNETTE: {vignette_summary} CONVERSATION: {json.dumps(conversation)}",
                "thinking": split_thinking_answer(diagnosis_raw)[0],
                "answer": split_thinking_answer(diagnosis_raw)[1],
                "output": diagnosis_raw,
                "turn_count": turn_count,
                "letter": letter,
                "gold_diagnosis": gold_label,
            }
        )

        # Handle END signal
        if turn_count >= 20:
            diagnosis_complete = True
            print(f"✅ Reached END for vignette {idx}. Moving to next.\n")

            prompt = f"""You are generating training data for a treatment planning reasoning model.

Create a THINKING section showing how a treatment reasoning model should develop comprehensive treatment plans with specific clinical reasoning.

FINAL DIAGNOSES: {diagnosis}

CLINICAL VIGNETTE SUMMARY: {vignette_summary}

CONVERSATION: {json.dumps(conversation)}

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
                    "input": f"""DIAGNOSIS: {diagnosis} VIGNETTE: {vignette_summary} CONVERSATION: {json.dumps(conversation)}""",  # Clean input string
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
            turn_count, vignette_summary, diagnosis, previous_questions, conversation
        )

        followup_result = questioner.ask(simple_prompt)
        raw_followup = followup_result["raw"]
        followup_question = followup_result["clean"]

        print("❓ Follow-up:", followup_question)
        questioning_doctor_outputs.append(
            {
                "vignette_index": idx,
                "input": f"VIGNETTE: {vignette_summary} DIAGNOSIS: {diagnosis} CONVERSATION: {json.dumps(conversation)}",
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
You are generating high-quality training data for a patient reasoning model grounded in structured clinical reasoning.

Your task is to simulate:
1. How a patient with the background in VIGNETTE_TEXT would internally process the FOLLOWUP_QUESTION from the doctor.
2. How the patient would naturally respond, based only on the information in the vignette.

Please respond in the following strict format:

THINKING: Describe the patient's thought process using ONLY information from the vignette and the doctor's follow-up question. Reflect on how the patient interprets the question, what they remember or physically feel (as stated in the vignette), how they emotionally respond to the question (if implied by the vignette), and how they decide what details are relevant to include in their answer.

ANSWER: Generate a natural-sounding patient reply that stays grounded entirely in the vignette, and directly answers the follow-up question. Do NOT introduce any new symptoms, details, or interpretations not already present in the vignette. DO not use ANY medical terminology or jargon. Not even words like "radiating" or "sharp". Just respond as the patient would, in their own words, based on their understanding of their condition.

CONTEXT:
- VIGNETTE_TEXT: {vignette_text}
- FOLLOWUP_QUESTION: {followup_question}
- CONVERATION: {json.dumps(conversation)}
"""

        patient_fb_result = patient.ask(prompt)
        raw_patient_fb = patient_fb_result["raw"]
        patient_followup_text = patient_fb_result["clean"]

        print("🗣️ Patient:", patient_followup_text)
        conversation.append(f"PATIENT: {patient_followup_text}")
        patient_response.append(
            {
                "vignette_index": idx,
                "input": f"VIGNETTE: {vignette_text} QUESTION: {followup_question} CONVERSATION: {json.dumps(conversation)}",
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

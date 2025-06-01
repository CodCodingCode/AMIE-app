import os
import json
from openai import OpenAI
import time
import multiprocessing
import shutil
from itertools import islice
import random

# Initialize OpenAI client
client = OpenAI(
    api_key="api"
)
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


def generate_gold_guided_prompt(base_prompt, gold_diagnosis, stage, vignette_summary):
    """
    Generate diagnostic prompts that provide strong guidance toward correct diagnosis
    """
    # Create contextual hints based on gold diagnosis
    diagnostic_hints = create_diagnostic_hints(gold_diagnosis, stage)

    # Add stage-specific strength
    guidance_strength = get_guidance_strength(stage)

    guided_prompt = f"""
    {base_prompt}
    
    DIAGNOSTIC GUIDANCE ({guidance_strength}):
    {diagnostic_hints}
    
    CRITICAL INSTRUCTIONS:
    - Prioritize conditions that match the clinical presentation patterns described above
    - Consider both common and atypical presentations of the suggested condition categories
    - Place higher emphasis on the primary consideration mentioned in guidance
    - If guidance suggests specific diagnostic categories, include them prominently in your differential
    """

    return guided_prompt


def get_guidance_strength(stage):
    """Return appropriate guidance strength based on conversation stage"""
    if stage == "early":
        return "Strong guidance - use to inform your broad differential"
    elif stage == "middle":
        return "Very strong guidance - prioritize these conditions"
    else:
        return "Critical guidance - this should be your primary consideration"


def create_diagnostic_hints(gold_diagnosis, stage):
    """
    Create strong, specific hints that guide toward correct diagnosis
    """
    # Enhanced database with more diseases and stronger guidance
    diagnostic_patterns = {
        # Cardiovascular - Enhanced
        "myocardial infarction": {
            "patterns": [
                "acute coronary syndrome presentations",
                "cardiac ischemic events",
                "chest pain with cardiac risk factors",
            ],
            "key_features": [
                "chest pain character and radiation patterns",
                "associated autonomic symptoms (nausea, sweating, SOB)",
                "cardiac risk factor assessment",
            ],
            "red_flags": [
                "acute coronary syndrome presentations",
                "hemodynamic instability",
                "troponin elevation patterns",
            ],
            "strong_indicators": [
                "crushing chest pain",
                "left arm radiation",
                "diaphoresis with chest discomfort",
                "cardiac risk factors present",
            ],
        },
        "hypertension": {
            "patterns": [
                "hypertensive syndromes",
                "elevated blood pressure conditions",
                "cardiovascular risk presentations",
            ],
            "key_features": [
                "blood pressure elevation patterns",
                "afternoon/evening headache timing",
                "stress-related symptom exacerbation",
            ],
            "red_flags": [
                "hypertensive emergency signs",
                "end-organ damage indicators",
            ],
            "strong_indicators": [
                "headaches worse in afternoon/evening",
                "dizziness with position changes",
                "stress making symptoms worse",
                "family history of hypertension",
            ],
        },
        "heart failure": {
            "patterns": [
                "cardiac pump dysfunction syndromes",
                "fluid retention conditions",
                "decreased cardiac output presentations",
            ],
            "key_features": [
                "exertional dyspnea patterns",
                "orthopnea and PND",
                "peripheral edema development",
            ],
            "red_flags": ["acute decompensation signs", "cardiogenic shock indicators"],
            "strong_indicators": [
                "shortness of breath with exertion",
                "swelling in legs/ankles",
                "difficulty breathing when lying flat",
                "fatigue with minimal activity",
            ],
        },
        # Respiratory - Enhanced
        "asthma": {
            "patterns": [
                "reversible airway obstruction",
                "bronchospastic conditions",
                "allergic respiratory syndromes",
            ],
            "key_features": [
                "wheezing and bronchospasm patterns",
                "trigger identification",
                "response to bronchodilator therapy",
            ],
            "red_flags": [
                "severe bronchospasm requiring emergency care",
                "respiratory failure indicators",
            ],
            "strong_indicators": [
                "wheezing sounds",
                "shortness of breath with triggers",
                "cough especially at night",
                "family history of asthma/allergies",
            ],
        },
        "pneumonia": {
            "patterns": [
                "infectious respiratory syndromes",
                "consolidative lung disease",
                "bacterial/viral pneumonic processes",
            ],
            "key_features": [
                "productive cough with fever",
                "chest pain with breathing",
                "systemic infection signs",
            ],
            "red_flags": ["sepsis indicators", "respiratory failure signs"],
            "strong_indicators": [
                "fever with cough",
                "chest pain when breathing",
                "thick colored sputum",
                "recent illness or exposure",
            ],
        },
        "copd": {
            "patterns": [
                "chronic obstructive pulmonary disease",
                "smoking-related lung disease",
                "progressive airway limitation",
            ],
            "key_features": [
                "chronic productive cough",
                "progressive dyspnea",
                "smoking history significance",
            ],
            "red_flags": [
                "acute exacerbation patterns",
                "respiratory failure development",
            ],
            "strong_indicators": [
                "long-term smoking history",
                "chronic morning cough",
                "increasing shortness of breath",
                "barrel chest appearance",
            ],
        },
        # Gastrointestinal - Enhanced
        "gastroesophageal reflux disease": {
            "patterns": [
                "acid reflux syndromes",
                "esophageal irritation conditions",
                "upper gastrointestinal symptoms",
            ],
            "key_features": [
                "heartburn after meals",
                "regurgitation patterns",
                "positional symptom variation",
            ],
            "red_flags": ["dysphagia development", "weight loss with reflux"],
            "strong_indicators": [
                "burning sensation in chest after eating",
                "symptoms worse when lying down",
                "sour taste in mouth",
                "symptoms improve with antacids",
            ],
        },
        "appendicitis": {
            "patterns": [
                "acute appendiceal inflammation",
                "right lower quadrant pain syndromes",
                "surgical abdomen presentations",
            ],
            "key_features": [
                "pain migration from periumbilical to RLQ",
                "McBurney's point tenderness",
                "fever with abdominal pain",
            ],
            "red_flags": ["peritonitis signs", "perforation indicators"],
            "strong_indicators": [
                "pain starting around navel then moving to right side",
                "pain worse with walking or coughing",
                "nausea and vomiting",
                "low-grade fever",
            ],
        },
        "peptic ulcer disease": {
            "patterns": [
                "gastroduodenal ulceration",
                "acid-peptic disorders",
                "H. pylori related conditions",
            ],
            "key_features": [
                "epigastric pain patterns",
                "meal-related symptom timing",
                "NSAID use history",
            ],
            "red_flags": ["GI bleeding indicators", "perforation signs"],
            "strong_indicators": [
                "burning stomach pain",
                "pain between meals or at night",
                "relief with food or antacids",
                "NSAID use history",
            ],
        },
        # Endocrine - Enhanced
        "diabetes mellitus": {
            "patterns": [
                "hyperglycemic syndromes",
                "insulin deficiency/resistance conditions",
                "metabolic dysfunction presentations",
            ],
            "key_features": [
                "polyuria and polydipsia patterns",
                "unexplained weight changes",
                "glucose metabolism disruption",
            ],
            "red_flags": ["diabetic ketoacidosis signs", "hyperosmolar states"],
            "strong_indicators": [
                "excessive urination and thirst",
                "unexplained weight loss",
                "fatigue and weakness",
                "slow healing wounds",
            ],
        },
        "hypothyroidism": {
            "patterns": [
                "thyroid hormone deficiency",
                "metabolic slowdown syndromes",
                "endocrine hypofunction",
            ],
            "key_features": [
                "fatigue and cold intolerance",
                "weight gain patterns",
                "cognitive slowing",
            ],
            "red_flags": ["myxedema coma signs", "severe hypothyroid complications"],
            "strong_indicators": [
                "persistent fatigue despite rest",
                "feeling cold when others are comfortable",
                "unexplained weight gain",
                "dry skin and hair loss",
            ],
        },
        "hyperthyroidism": {
            "patterns": [
                "thyroid hormone excess",
                "metabolic acceleration syndromes",
                "thyrotoxic conditions",
            ],
            "key_features": [
                "palpitations and tremor",
                "heat intolerance patterns",
                "weight loss with increased appetite",
            ],
            "red_flags": ["thyroid storm indicators", "cardiac complications"],
            "strong_indicators": [
                "rapid heartbeat or palpitations",
                "trembling hands",
                "weight loss despite eating more",
                "feeling hot and sweaty",
            ],
        },
        # Neurological - Enhanced
        "stroke": {
            "patterns": [
                "acute cerebrovascular events",
                "focal neurological deficits",
                "brain vascular occlusion/hemorrhage",
            ],
            "key_features": [
                "sudden onset neurological symptoms",
                "focal weakness patterns",
                "speech or vision changes",
            ],
            "red_flags": ["large vessel occlusion signs", "hemorrhagic transformation"],
            "strong_indicators": [
                "sudden weakness on one side",
                "facial drooping",
                "slurred speech",
                "sudden severe headache",
            ],
        },
        "migraine": {
            "patterns": [
                "primary headache disorders",
                "neurovascular headache syndromes",
                "episodic severe headache",
            ],
            "key_features": [
                "unilateral throbbing headache",
                "associated nausea/vomiting",
                "photophobia and phonophobia",
            ],
            "red_flags": ["status migrainosus", "medication overuse headache"],
            "strong_indicators": [
                "severe one-sided headache",
                "nausea with headache",
                "sensitivity to light and sound",
                "family history of migraines",
            ],
        },
        "seizure disorder": {
            "patterns": [
                "epileptic syndromes",
                "seizure activity disorders",
                "neuronal hyperexcitability",
            ],
            "key_features": [
                "episodic altered consciousness",
                "motor activity patterns",
                "postictal state description",
            ],
            "red_flags": ["status epilepticus", "new onset seizures in adults"],
            "strong_indicators": [
                "episodes of losing awareness",
                "involuntary movements",
                "confusion after episodes",
                "tongue biting or incontinence",
            ],
        },
        # Musculoskeletal - Enhanced
        "osteoarthritis": {
            "patterns": [
                "degenerative joint disease",
                "mechanical arthritis",
                "cartilage deterioration syndromes",
            ],
            "key_features": [
                "joint pain with activity",
                "morning stiffness <30 minutes",
                "weight-bearing joint involvement",
            ],
            "red_flags": ["rapid joint destruction", "systemic inflammatory signs"],
            "strong_indicators": [
                "joint pain worse with use",
                "stiffness that improves with movement",
                "pain in knees, hips, or hands",
                "age over 50",
            ],
        },
        "rheumatoid arthritis": {
            "patterns": [
                "inflammatory arthritis",
                "autoimmune joint disease",
                "systemic inflammatory conditions",
            ],
            "key_features": [
                "symmetrical joint involvement",
                "prolonged morning stiffness",
                "small joint predilection",
            ],
            "red_flags": [
                "extra-articular manifestations",
                "joint destruction progression",
            ],
            "strong_indicators": [
                "morning stiffness lasting hours",
                "swelling in multiple joints",
                "symmetrical joint involvement",
                "fatigue and malaise",
            ],
        },
        "fibromyalgia": {
            "patterns": [
                "chronic widespread pain",
                "central sensitization syndromes",
                "pain amplification disorders",
            ],
            "key_features": [
                "widespread tender points",
                "sleep disturbance patterns",
                "fatigue association",
            ],
            "red_flags": [
                "underlying inflammatory conditions",
                "systemic disease masquerading",
            ],
            "strong_indicators": [
                "widespread body pain",
                "tender points on examination",
                "chronic fatigue",
                "sleep problems",
            ],
        },
        # Mental Health - Enhanced
        "depression": {
            "patterns": [
                "major depressive disorders",
                "mood disorder syndromes",
                "anhedonia presentations",
            ],
            "key_features": [
                "persistent depressed mood",
                "anhedonia patterns",
                "neurovegetative symptoms",
            ],
            "red_flags": ["suicidal ideation", "psychotic features"],
            "strong_indicators": [
                "persistent sad or empty mood",
                "loss of interest in activities",
                "sleep disturbances",
                "feelings of worthlessness",
            ],
        },
        "anxiety disorders": {
            "patterns": [
                "anxiety spectrum conditions",
                "panic disorder syndromes",
                "phobic disorders",
            ],
            "key_features": [
                "excessive worry patterns",
                "physical anxiety symptoms",
                "avoidance behaviors",
            ],
            "red_flags": ["panic attack complications", "severe functional impairment"],
            "strong_indicators": [
                "excessive worry or fear",
                "physical symptoms (racing heart, sweating)",
                "avoidance of situations",
                "restlessness or feeling on edge",
            ],
        },
        "bipolar disorder": {
            "patterns": [
                "mood cycling disorders",
                "manic-depressive syndromes",
                "episodic mood disturbances",
            ],
            "key_features": [
                "manic episode history",
                "mood cycling patterns",
                "functional impairment during episodes",
            ],
            "red_flags": ["mixed episodes", "rapid cycling patterns"],
            "strong_indicators": [
                "periods of elevated mood",
                "decreased need for sleep during high periods",
                "alternating with depression",
                "impulsive behavior during episodes",
            ],
        },
        # Infectious Diseases - New
        "urinary tract infection": {
            "patterns": [
                "bacterial urinary infections",
                "cystitis syndromes",
                "urogenital infectious processes",
            ],
            "key_features": [
                "dysuria patterns",
                "urinary frequency/urgency",
                "suprapubic discomfort",
            ],
            "red_flags": ["pyelonephritis signs", "sepsis indicators"],
            "strong_indicators": [
                "burning with urination",
                "frequent urge to urinate",
                "cloudy or strong-smelling urine",
                "pelvic pain in women",
            ],
        },
        "sinusitis": {
            "patterns": [
                "paranasal sinus inflammation",
                "rhinosinusitis syndromes",
                "upper respiratory infections",
            ],
            "key_features": [
                "facial pain/pressure",
                "nasal congestion patterns",
                "post-nasal drainage",
            ],
            "red_flags": ["orbital complications", "intracranial extension"],
            "strong_indicators": [
                "facial pain or pressure",
                "thick nasal discharge",
                "reduced sense of smell",
                "headache over sinuses",
            ],
        },
        # Dermatological - New
        "eczema": {
            "patterns": [
                "atopic dermatitis syndromes",
                "chronic inflammatory skin conditions",
                "allergic skin reactions",
            ],
            "key_features": [
                "pruritic skin lesions",
                "chronic/relapsing course",
                "atopic triad association",
            ],
            "red_flags": [
                "secondary bacterial infection",
                "severe widespread involvement",
            ],
            "strong_indicators": [
                "itchy, red, inflamed skin",
                "dry or scaly patches",
                "family history of allergies",
                "symptoms worse with certain triggers",
            ],
        },
        # Additional Common Conditions
        "kidney stones": {
            "patterns": [
                "renal calculi syndromes",
                "nephrolithiasis presentations",
                "urinary stone disease",
            ],
            "key_features": [
                "severe flank pain",
                "colicky pain patterns",
                "hematuria presence",
            ],
            "red_flags": ["complete obstruction", "infection with obstruction"],
            "strong_indicators": [
                "severe back or side pain",
                "pain that comes in waves",
                "blood in urine",
                "nausea and vomiting with pain",
            ],
        },
        "anemia": {
            "patterns": [
                "hemoglobin deficiency syndromes",
                "oxygen carrying capacity reduction",
                "hematologic disorders",
            ],
            "key_features": [
                "fatigue and weakness",
                "pallor patterns",
                "exertional dyspnea",
            ],
            "red_flags": ["severe anemia complications", "underlying malignancy"],
            "strong_indicators": [
                "persistent fatigue and weakness",
                "pale skin or nail beds",
                "shortness of breath with activity",
                "cold hands and feet",
            ],
        },
    }

    # Enhanced matching with partial word matching
    gold_lower = gold_diagnosis.lower()
    pattern_info = None

    # First try exact matching
    for condition, info in diagnostic_patterns.items():
        if condition == gold_lower:
            pattern_info = info
            break

    # Then try partial matching
    if not pattern_info:
        for condition, info in diagnostic_patterns.items():
            condition_words = condition.split()
            gold_words = gold_lower.split()

            # Check if any significant words match
            if any(word in gold_lower for word in condition_words) or any(
                word in condition for word in gold_words
            ):
                pattern_info = info
                break

    # If no specific pattern found, create strong generic guidance
    if not pattern_info:
        return f"""
        CRITICAL: This patient's presentation matches the gold standard diagnosis pattern.
        
        PRIMARY FOCUS: Consider conditions that present with the exact clinical features described in this vignette.
        
        ESSENTIAL ACTIONS:
        - Prioritize diagnoses that match the specific symptom complex
        - Consider both typical and atypical presentations
        - Pay special attention to temporal patterns and associated symptoms
        - Include the most likely condition prominently in your differential
        
        The correct diagnosis should be strongly suggested by the clinical presentation described.
        """

    # Stage-specific enhanced guidance
    if stage == "early":  # 10 diagnoses
        return f"""
        STRONG DIAGNOSTIC GUIDANCE - Early Stage:
        
        PRIMARY CONSIDERATION: {pattern_info['patterns'][0]}
        
        KEY CLINICAL INDICATORS TO PRIORITIZE:
        {chr(10).join(f"- {indicator}" for indicator in pattern_info['strong_indicators'])}
        
        SECONDARY CONSIDERATIONS: {', '.join(pattern_info['patterns'][1:])}.
        
        CRITICAL FEATURES TO EVALUATE: {', '.join(pattern_info['key_features'])}.
        
        IMPORTANT: The primary consideration should be included prominently (top 3) in your differential diagnosis.
        Include both common and less common conditions, but prioritize those matching the strong indicators above.
        """

    elif stage == "middle":  # 5 diagnoses
        return f"""
        VERY STRONG DIAGNOSTIC GUIDANCE - Middle Stage:
        
        TOP PRIORITY: {pattern_info['patterns'][0]}
        
        CRITICAL INDICATORS PRESENT:
        {chr(10).join(f"- {indicator}" for indicator in pattern_info['strong_indicators'][:3])}
        
        FOCUS AREAS: {', '.join(pattern_info['patterns'][:2])}.
        
        ESSENTIAL FEATURES: {', '.join(pattern_info['key_features'][:2])}.
        
        CRITICAL: Based on the clinical presentation, {pattern_info['patterns'][0]} should be your #1 or #2 consideration.
        Narrow to conditions most consistent with the strong indicators listed above.
        """

    else:  # Late stage - 1-3 diagnoses
        return f"""
        CRITICAL DIAGNOSTIC GUIDANCE - Final Stage:
        
        MOST LIKELY DIAGNOSIS: {pattern_info['patterns'][0]}
        
        DEFINITIVE INDICATORS:
        {chr(10).join(f"- {indicator}" for indicator in pattern_info['strong_indicators'][:2])}
        
        KEY CONFIRMATORY FEATURES: {pattern_info['key_features'][0]}.
        
        RED FLAGS TO EVALUATE: {', '.join(pattern_info['red_flags'])}.
        
        FINAL INSTRUCTION: The clinical presentation strongly suggests {pattern_info['patterns'][0]}. 
        This should be your primary diagnosis unless there are compelling contraindications.
        """


def generate_guided_questioner_prompt(base_prompt, gold_diagnosis, current_vignette):
    """
    Generate questioning prompts that strongly guide toward information relevant to gold diagnosis
    """
    # Get relevant questions for the gold diagnosis
    relevant_questions = get_relevant_questions(gold_diagnosis, current_vignette)

    guided_prompt = f"""
    {base_prompt}
    
    PRIORITY CLINICAL FOCUS AREAS:
    {relevant_questions}
    
    QUESTIONING STRATEGY:
    - Ask questions that explore the priority areas listed above
    - Prioritize gathering information that confirms or rules out the suggested conditions
    - Maintain natural conversation flow while focusing on diagnostically relevant information
    - Do not directly mention specific diagnoses, but guide toward relevant symptom exploration
    
    Your questions should efficiently gather the most diagnostically valuable information.
    """

    return guided_prompt


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
        
        STEP 6 - CLINICAL IMPLICATIONS:
        Finally, let me determine the clinical implications of these communication patterns.
        - How reliable is the current vignette? <assessment>
        - What critical information are we missing? <gaps>
        - What should the doctor probe for next? <recommendations>
        
        ANSWER:
        COMMUNICATION_ANALYSIS:
        - Pattern observed: <description of how patient is communicating>
        - Bias detected: <what kind of bias is affecting their reporting>
        - Confidence level: <high/medium/low>
        - Reasoning: <why I believe this based on my step-by-step analysis>
        
        LIKELY_HIDDEN_INFORMATION:
        - Minimized symptoms: <symptoms patient is downplaying + reasoning>
        - Withheld information: <information patient may be embarrassed to share + reasoning>
        - Amplified concerns: <symptoms patient may be exaggerating + reasoning>
        - Temporal distortions: <timeline issues or sequence problems + reasoning>
        
        OBJECTIVE_CLINICAL_PICTURE:
        Based on my Chain of Thought analysis, the unbiased vignette should probably include:
        <Detailed reconstruction accounting for identified biases with reasoning for each adjustment>
        
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


def get_relevant_questions(gold_diagnosis, current_vignette):
    """
    Suggest specific, targeted question areas based on gold diagnosis
    """
    question_guidance = {
        "myocardial infarction": [
            "chest pain characteristics, quality, radiation patterns",
            "associated symptoms (nausea, sweating, shortness of breath)",
            "cardiac risk factors (smoking, diabetes, hypertension, family history)",
            "activity relationship and onset timing",
            "previous cardiac events or procedures",
        ],
        "hypertension": [
            "blood pressure history and measurements",
            "headache timing patterns (especially afternoon/evening)",
            "family history of hypertension or heart disease",
            "stress factors and lifestyle assessment",
            "medication history and compliance",
        ],
        "asthma": [
            "breathing pattern details and wheeze assessment",
            "trigger identification (allergens, exercise, cold air)",
            "exercise tolerance and activity limitations",
            "medication response history (inhalers, bronchodilators)",
            "family history of asthma or allergies",
        ],
        "diabetes mellitus": [
            "polyuria and polydipsia symptoms (excessive urination/thirst)",
            "weight changes (loss or gain patterns)",
            "family history of diabetes assessment",
            "energy and fatigue patterns throughout day",
            "wound healing and infection history",
        ],
        "depression": [
            "mood and energy patterns over time",
            "sleep and appetite changes",
            "functional impact on daily activities",
            "interest and motivation levels",
            "thoughts of self-harm or suicide (when appropriate)",
        ],
        "anxiety disorders": [
            "worry patterns and anxiety triggers",
            "physical symptoms during anxious episodes",
            "avoidance behaviors and functional impact",
            "panic attack symptoms if present",
            "social and occupational functioning",
        ],
        "fibromyalgia": [
            "widespread pain distribution and quality",
            "sleep disturbance patterns and quality",
            "fatigue characteristics and timing",
            "functional impact on daily activities",
            "tender point assessment and pain triggers",
        ],
        "osteoarthritis": [
            "joint pain patterns and affected joints",
            "morning stiffness duration and quality",
            "activity-related pain changes",
            "functional limitations in daily activities",
            "previous joint injuries or family history",
        ],
        "rheumatoid arthritis": [
            "joint inflammation patterns and symmetry",
            "morning stiffness duration (especially >1 hour)",
            "systemic symptoms (fatigue, malaise)",
            "family history of autoimmune conditions",
            "functional decline and disability progression",
        ],
        "gastroesophageal reflux disease": [
            "heartburn timing and food relationships",
            "regurgitation and acid taste symptoms",
            "positional factors (lying down, bending over)",
            "medication response to antacids",
            "dietary triggers and lifestyle factors",
        ],
        "urinary tract infection": [
            "urinary symptoms (burning, frequency, urgency)",
            "urine appearance and odor changes",
            "pelvic or suprapubic pain",
            "fever or systemic symptoms",
            "previous UTI history and risk factors",
        ],
        "migraine": [
            "headache characteristics (location, quality, severity)",
            "associated symptoms (nausea, light/sound sensitivity)",
            "trigger identification and patterns",
            "family history of migraines",
            "medication response and headache diary",
        ],
        "pneumonia": [
            "cough characteristics and sputum production",
            "fever patterns and chills",
            "chest pain with breathing",
            "recent illness or exposure history",
            "vaccination status and risk factors",
        ],
    }

    # Enhanced matching for question guidance
    gold_lower = gold_diagnosis.lower()

    # Try exact match first
    if gold_lower in question_guidance:
        questions = question_guidance[gold_lower]
        return f"HIGH PRIORITY - Focus questioning on: {'; '.join(questions)}"

    # Try partial matching
    for condition, questions in question_guidance.items():
        if any(word in gold_lower for word in condition.split()) or any(
            word in condition for word in gold_lower.split()
        ):
            return f"PRIORITY FOCUS - Ask about: {'; '.join(questions)}"


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


def clean_diagnosis_output(raw_output):
    """Clean diagnosis output to only include THINKING and ANSWER sections"""
    lines = raw_output.split("\n")
    cleaned_lines = []
    in_valid_section = False

    for line in lines:
        line_stripped = line.strip()

        # Check if we're starting THINKING or ANSWER section
        if line_stripped.startswith("THINKING:") or line_stripped.startswith("ANSWER:"):
            in_valid_section = True
            cleaned_lines.append(line)
        # Stop at unwanted content
        elif (
            line_stripped.startswith("**Note:")
            or line_stripped.startswith("Note:")
            or line_stripped.startswith("**Additional:")
            or line_stripped.startswith("Additional:")
            or line_stripped.startswith("**Further:")
            or line_stripped.startswith("Further:")
            or line_stripped.startswith("**Recommendation:")
            or line_stripped.startswith("Recommendation:")
        ):
            break
        # Continue adding lines if we're in a valid section
        elif in_valid_section:
            cleaned_lines.append(line)

    return "\n".join(cleaned_lines).strip()


# === Updated Diagnosis Prompt Templates ===
EARLY_DIAGNOSIS_PROMPT = """You are a board-certified diagnostician.

Your task is to:
- Generate a list of 10 plausible diagnoses based on the patient's presentation.
- For each diagnosis, provide a brief justification for its consideration.

Previously asked questions: {prev_questions}

Vignette:
{vignette}
Turn count: {turn_count}

CRITICAL: You must respond ONLY in the exact format below. Do not add any notes, recommendations, further evaluations, or additional text after the ANSWER section.

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

STOP HERE. Do not add notes, recommendations, or additional text."""

MIDDLE_DIAGNOSIS_PROMPT = """You are a board-certified diagnostician.

Your task is to:
- Refine the differential diagnosis list to the 5 most probable conditions.
- Provide a detailed justification for each, considering the patient's data and previous discussions.

Previously asked questions: {prev_questions}

Vignette:
{vignette}
Turn count: {turn_count}

CRITICAL: You must respond ONLY in the exact format below. Do not add any notes, recommendations, or additional text after the ANSWER section.

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

STOP HERE. Do not add notes, recommendations, or additional text."""

LATE_DIAGNOSIS_PROMPT = """You are a board-certified diagnostician.

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

CRITICAL: You must respond ONLY in the exact format below. Do not add any notes, recommendations, or additional text.

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

STOP HERE. Do not add notes, recommendations, or additional text."""


# === Diagnosis Logic with Cleaning ===
def get_diagnosis_with_cleaning(
    turn_count, gold_label, vignette_summary, previous_questions, diagnoser
):
    """Get diagnosis with proper cleaning and updated prompts"""

    if turn_count < 6:
        base_prompt = EARLY_DIAGNOSIS_PROMPT
        stage = "early"
    elif turn_count >= 5 and turn_count < 11:
        base_prompt = MIDDLE_DIAGNOSIS_PROMPT
        stage = "middle"
    else:
        base_prompt = LATE_DIAGNOSIS_PROMPT
        stage = "late"

    # Add gold diagnosis guidance
    guided_prompt = generate_gold_guided_prompt(
        base_prompt, gold_label, stage, vignette_summary
    )

    # Get raw diagnosis
    raw_diagnosis = diagnoser.ask(
        guided_prompt.format(
            prev_questions=json.dumps(previous_questions),
            vignette=vignette_summary,
            turn_count=turn_count,
        )
    )

    # Clean the output
    cleaned_diagnosis = clean_diagnosis_output(raw_diagnosis)

    return cleaned_diagnosis


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
    global conversation, patient_response, summarizer_outputs, diagnosing_doctor_outputs, questioning_doctor_outputs, treatment_plans, behavioral_analyses, patient_interpretations

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
    
    # NEW: Store all behavioral analyses for memory
    all_behavioral_analyses = []
    all_patient_interpretations = []

    while not diagnosis_complete:
        # NEW: Only use behavioral analysis for first 5 exchanges (turn_count 0, 2, 4, 6, 8)
        if turn_count <= 8:
            # Enhanced behavioral analysis with memory of previous analyses
            behavioral_analysis = detect_patient_behavior_cues_enhanced_with_memory(
                conversation, patient_response, all_behavioral_analyses
            )
            all_behavioral_analyses.append(behavioral_analysis)
            behavioral_analyses.append(
                {
                    "vignette_index": idx,
                    "turn_count": turn_count,
                    "analysis": behavioral_analysis,
                }
            )
            print(f"🧠 Enhanced Behavioral Analysis (Turn {turn_count//2 + 1}): {behavioral_analysis[:200]}...")

            # Patient Interpretation with memory of previous interpretations
            patient_interpreter = PatientInterpreter()
            patient_interpretation = patient_interpreter.interpret_patient_communication_with_memory(
                conversation, behavioral_analysis, prev_vignette_summary, all_patient_interpretations
            )
            all_patient_interpretations.append(patient_interpretation)
            patient_interpretations.append(
                {
                    "vignette_index": idx,
                    "turn_count": turn_count,
                    "interpretation": patient_interpretation,
                }
            )
            print(f"🔍 Patient Interpretation (Turn {turn_count//2 + 1}): {patient_interpretation[:200]}...")

            # Generate unbiased vignette using interpreter insights
            joined_conversation = "\\n".join(conversation)
            vignette_summary = generate_unbiased_vignette(
                conversation, prev_vignette_summary, patient_interpretation
            )
        else:
            # NEW: After turn 8, use standard summarizer without behavioral analysis
            print(f"🔄 Using standard summarizer (Turn {turn_count//2 + 1} - beyond behavioral analysis phase)")
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
            # Use last known behavioral analysis for empathy but no new interpretation
            behavioral_analysis = all_behavioral_analyses[-1] if all_behavioral_analyses else f"Expected behavioral cues: {', '.join(behavior_config.get('empathy_cues', []))}"

        summarizer_outputs.append(
            {
                "vignette_index": idx,
                "input": joined_conversation,
                "output": vignette_summary,
                "patient_interpretation": all_patient_interpretations[-1] if all_patient_interpretations else "No interpretation - beyond behavioral phase",
                "turn_count": turn_count,
                "behavioral_phase": turn_count <= 8
            }
        )

        prev_vignette_summary = vignette_summary

        if "ANSWER:" in vignette_summary:
            vignette_summary = vignette_summary.split("ANSWER:")[1].strip()
        else:
            vignette_summary = vignette_summary

        # === UPDATED DIAGNOSIS LOGIC WITH CLEANING ===
        diagnosis = get_diagnosis_with_cleaning(
            turn_count, gold_label, vignette_summary, previous_questions, diagnoser
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
                "behavioral_phase": turn_count <= 8
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
                    f"⚠️ Model said END before 15 turns. Ignoring END due to insufficient conversation length."
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
                "behavioral_phase": turn_count <= 8
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
        "behavioral_analysis_turns": len(all_behavioral_analyses),
        "total_turns": turn_count // 2
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
    with open(f"2patient_interpretations/interpretation_{idx}.json", "w") as f:
        json.dump(patient_interpretations, f, indent=2)

    return {
        "vignette_index": idx,
        "patient_response": patient_response,
        "summarizer_outputs": summarizer_outputs,
        "diagnosing_doctor_outputs": diagnosing_doctor_outputs,
        "questioning_doctor_outputs": questioning_doctor_outputs,
        "treatment_plans": treatment_plans,
        "behavior_metadata": behavior_metadata,
        "behavioral_analyses": behavioral_analyses,
        "patient_interpretations": patient_interpretations,
        "gold_diagnosis": gold_label,
    }


# === Enhanced behavioral analysis with memory ===
def detect_patient_behavior_cues_enhanced_with_memory(conversation_history, patient_responses, previous_analyses):
    """Enhanced version that provides more detailed behavioral analysis using Chain of Thought reasoning with memory"""
    cue_detector = RoleResponder(
        """You are a behavioral psychologist specializing in patient communication patterns.
        You're expert at identifying subtle signs of information withholding, symptom minimization, 
        anxiety amplification, and other communication biases that affect clinical assessment.
        
        You use Chain of Thought reasoning to systematically analyze patient behavior patterns and can
        build on your previous analyses to create a consistent understanding of the patient over time."""
    )

    recent_responses = patient_responses[-3:]
    
    # Format previous analyses for context
    previous_analyses_context = ""
    if previous_analyses:
        previous_analyses_context = f"""
        
        PREVIOUS BEHAVIORAL ANALYSES:
        {json.dumps(previous_analyses[-2:], indent=2)}  # Last 2 analyses for context
        
        CONSISTENCY GOAL: Build on previous analyses to create a coherent understanding of this patient's communication style. 
        Note any changes in behavior or confirmation of previous patterns.
        """

    analysis = cue_detector.ask(
        f"""
    Use Chain of Thought reasoning to analyze these patient responses for detailed behavioral patterns:
    
    RECENT PATIENT RESPONSES:
    {json.dumps(recent_responses, indent=2)}
    
    CONVERSATION CONTEXT:
    {json.dumps(conversation_history[-6:], indent=2)}
    
    {previous_analyses_context}
    
    YOU MUST RESPOND IN THE FOLLOWING FORMAT:
    
    THINKING:
    Use Chain of Thought Analysis:
    
    STEP 1 - CONSISTENCY CHECK:
    {"First, let me review my previous analyses of this patient and identify consistent patterns." if previous_analyses else "This is my first analysis of this patient."}
    - Consistent patterns from previous turns: <identify recurring behaviors>
    - Changes observed: <note any behavioral evolution>
    - Standardization progress: <how patient behavior is stabilizing>
    
    STEP 2 - LANGUAGE ANALYSIS:
    Let me examine the specific words and phrases the patient uses.
    - Minimizing language: <identify phrases like "just", "only", "a little", "not that bad">
    - Amplifying language: <identify phrases like "terrible", "worst", "unbearable", "excruciating">
    - Vague language: <identify non-specific descriptions, "sort of", "kind of", "maybe">
    - Emotional language: <identify fear, embarrassment, frustration indicators>
    
    STEP 3 - RESPONSE PATTERN ANALYSIS:
    Now let me analyze how they respond to different types of questions.
    - Response length: <long/short responses and what triggers each>
    - Directness: <do they answer directly or deflect?>
    - Information volunteering: <do they offer additional details or wait to be asked?>
    - Consistency: <are their responses consistent across similar questions?>
    
    STEP 4 - BEHAVIORAL INDICATOR IDENTIFICATION:
    Based on the language and response patterns, let me identify specific behavioral indicators.
    - Information withholding signs: <evidence of reluctance to share specific types of information>
    - Minimization behaviors: <evidence they're downplaying symptoms>
    - Amplification patterns: <evidence they're exaggerating concerns>
    - Embarrassment/shame signals: <evidence of discomfort with certain topics>
    - Confusion/memory issues: <evidence of timeline or factual inconsistencies>
    - Family influence: <evidence others are affecting their responses>
    
    STEP 5 - BIAS SEVERITY ASSESSMENT:
    Now let me evaluate how severely these biases are affecting their communication.
    - Primary bias type: <main communication bias identified>
    - Severity level: <mild/moderate/severe with reasoning>
    - Areas most affected: <which symptoms/topics are most biased>
    - Reliability assessment: <how much to trust their self-reporting>
    - Behavioral evolution: <how their communication style is changing over time>
    
    ANSWER:
    COMMUNICATION_PATTERNS:
    - Language choices: <vague vs specific, emotional vs clinical + examples>
    - Information flow: <forthcoming vs reluctant, organized vs scattered + evidence>
    - Response style: <elaborate vs minimal, direct vs tangential + patterns>
    - Consistency with previous analysis: <how this matches or differs from previous patterns>
    
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
    - Behavioral stability: <how consistent this patient's patterns are becoming>
    
    CLINICAL_IMPLICATIONS:
    - Information likely missing: <what they're probably not telling you + reasoning>
    - Symptoms probably minimized: <what's worse than they say + evidence>
    - Concerns probably amplified: <what they're over-worried about + evidence>
    - True timeline: <actual progression vs reported progression + reasoning>
    - Standardization progress: <how their communication is becoming more reliable>
    """
    )

    return analysis


# === Enhanced Patient Interpreter with memory ===
class PatientInterpreter:
    """Agent specialized in reading patient communication patterns and extracting unbiased clinical information using Chain of Thought reasoning"""

    def __init__(self):
        self.role_instruction = """You are a specialized clinical psychologist and communication expert trained to interpret patient communication patterns.
        
        Your expertise includes:
        - Recognizing when patients minimize, exaggerate, or withhold information
        - Understanding cultural and psychological factors affecting patient communication
        - Translating patient language into objective clinical descriptions
        - Identifying implicit symptoms and concerns not directly stated
        - Building consistent understanding of patients over multiple interactions
        
        You use systematic Chain of Thought reasoning to analyze patient communication step-by-step.
        You help extract the true clinical picture from biased or incomplete patient presentations."""

        self.responder = RoleResponder(self.role_instruction)

    def interpret_patient_communication_with_memory(
        self, conversation_history, detected_behavior, current_vignette, previous_interpretations
    ):
        """Analyze patient communication to extract unbiased clinical information using Chain of Thought reasoning with memory"""

        # Format previous interpretations for context
        previous_context = ""
        if previous_interpretations:
            previous_context = f"""
            
            PREVIOUS INTERPRETATIONS:
            {json.dumps(previous_interpretations[-2:], indent=2)}  # Last 2 interpretations for context
            
            STANDARDIZATION GOAL: Build on previous interpretations to create a consistent, evolving understanding
            of this patient's true clinical picture. Note how their communication patterns are stabilizing.
            """

        interpretation_prompt = f"""
        TASK: Use Chain of Thought reasoning to analyze this patient's communication pattern and extract the true clinical picture.
        
        DETECTED PATIENT BEHAVIOR: {detected_behavior}
        
        CONVERSATION HISTORY:
        {json.dumps(conversation_history[-6:], indent=2)}  # Last 6 exchanges
        
        CURRENT VIGNETTE SUMMARY:
        {current_vignette}
        
        {previous_context}
        
        YOU MUST RESPOND IN THE FOLLOWING FORMAT:
        
        THINKING:
        Use the following Chain of Thought process:
        
        STEP 1 - INITIAL OBSERVATION:
        Let me first observe what the patient is literally saying versus how they're saying it.
        - Direct statements made: <list explicit statements>
        - Communication style observed: <tone, word choice, length of responses>
        - Non-verbal cues in language: <hesitation, minimization, amplification>
        - Consistency with previous patterns: <how this matches previous observations>
        
        STEP 2 - PATTERN RECOGNITION:
        Now I'll identify specific communication patterns that suggest bias.
        - If the patient uses minimizing language ("just a little", "not that bad"), this suggests they may be downplaying severity
        - If the patient gives vague responses when asked direct questions, this suggests potential withholding
        - If the patient uses catastrophic language ("terrible", "worst pain ever"), this suggests potential amplification
        - If timeline responses are inconsistent or vague, this suggests memory issues or confusion
        - Pattern evolution: <how these patterns are changing or stabilizing over time>
        
        STEP 3 - BIAS IDENTIFICATION:
        Based on the patterns, let me identify the specific biases affecting their reporting.
        - Type of bias detected: <minimization/amplification/withholding/confusion>
        - Evidence for this bias: <specific examples from conversation>
        - Severity of bias: <how much it's affecting their reporting>
        - Bias consistency: <how stable this bias pattern is becoming>
        
        STEP 4 - HIDDEN INFORMATION ANALYSIS:
        Now I'll deduce what information might be missing or distorted.
        - What symptoms might be worse than reported? <reasoning>
        - What information might they be embarrassed to share? <reasoning>
        - What timeline distortions might exist? <reasoning>
        - What associated symptoms might they be omitting? <reasoning>
        - Integration with previous findings: <how this builds on previous interpretations>
        
        STEP 5 - OBJECTIVE RECONSTRUCTION:
        Let me reconstruct what the objective clinical picture likely looks like.
        - Taking minimization into account: <adjusted symptom severity>
        - Accounting for withheld information: <likely missing symptoms>
        - Correcting timeline distortions: <more accurate progression>
        - Considering amplified concerns: <appropriately scaled worries>
        - Cumulative understanding: <how the complete picture is emerging>
        
        STEP 6 - CLINICAL IMPLICATIONS:
        Finally, let me determine the clinical implications of these communication patterns.
        - How reliable is the current vignette? <assessment>
        - What critical information are we missing? <gaps>
        - What should the doctor probe for next? <recommendations>
        - Standardization assessment: <how the patient's communication is becoming more reliable>
        
        ANSWER:
        COMMUNICATION_ANALYSIS:
        - Pattern observed: <description of how patient is communicating>
        - Bias detected: <what kind of bias is affecting their reporting>
        - Confidence level: <high/medium/low>
        - Reasoning: <why I believe this based on my step-by-step analysis>
        - Pattern stability: <how consistent this patient's behavior is becoming>
        
        LIKELY_HIDDEN_INFORMATION:
        - Minimized symptoms: <symptoms patient is downplaying + reasoning>
        - Withheld information: <information patient may be embarrassed to share + reasoning>
        - Amplified concerns: <symptoms patient may be exaggerating + reasoning>
        - Temporal distortions: <timeline issues or sequence problems + reasoning>
        
        OBJECTIVE_CLINICAL_PICTURE:
        Based on my Chain of Thought analysis and previous interpretations, the unbiased vignette should probably include:
        <Detailed reconstruction accounting for identified biases with reasoning for each adjustment>
        
        RECOMMENDED_PROBING:
        - Specific questions to ask: <targeted questions to get missing information + rationale>
        - Approach strategy: <how to ask sensitively + psychological reasoning>
        - Priority order: <which questions to ask first and why>
        - Standardization progress: <how the patient is becoming more forthcoming>
        """

        return self.responder.ask(interpretation_prompt)

    # Keep the old method for compatibility
    def interpret_patient_communication(self, conversation_history, detected_behavior, current_vignette):
        """Fallback method for compatibility"""
        return self.interpret_patient_communication_with_memory(
            conversation_history, detected_behavior, current_vignette, []
        )


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
        "new_data_gen/actual_data_gen/medical_vignettes_100_diseases.json",
        "r",
    ) as f:
        data = json.load(f)

    flattened_vignettes = []

    # Check the structure of your JSON file
    print(
        "JSON keys:",
        list(data.keys()) if isinstance(data, dict) else f"Type: {type(data)}",
    )

    # Handle both possible structures
    if "vignettes" in data:
        # Structure like: {"metadata": {...}, "vignettes": {"Disease": [vignettes...]}}
        vignette_dict = data["vignettes"]
        for disease, vignettes in vignette_dict.items():
            # Only process if we have a list of vignettes
            if not isinstance(vignettes, list):
                continue
            for vignette in vignettes:
                flattened_vignettes.append((disease, vignette))

    elif isinstance(data, dict):
        # Direct structure: {"Disease": [vignettes...]}
        for disease, vignettes in data.items():
            # Skip metadata if it exists
            if disease == "metadata":
                continue
            # Only process if we have a list of vignettes
            if not isinstance(vignettes, list):
                continue
            for vignette in vignettes:
                flattened_vignettes.append((disease, vignette))

    elif isinstance(data, list):
        # List structure: [{"disease": "...", "vignette": "..."}, ...]
        for item in data:
            if isinstance(item, dict) and "disease" in item and "vignette" in item:
                flattened_vignettes.append((item["disease"], item["vignette"]))
            elif (
                isinstance(item, dict)
                and "gold_diagnosis" in item
                and "vignette" in item
            ):
                flattened_vignettes.append((item["gold_diagnosis"], item["vignette"]))

    else:
        raise ValueError(f"Unexpected JSON structure. Top level is: {type(data)}")

    print(f"Loaded {len(flattened_vignettes)} total vignettes")
    if flattened_vignettes:
        print(
            f"First example: Disease='{flattened_vignettes[0][0]}', Vignette preview: '{flattened_vignettes[0][1][:100]}...'"
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

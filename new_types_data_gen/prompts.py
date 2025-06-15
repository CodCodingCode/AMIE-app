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


# === Patient Interpreter Prompts ===
PATIENT_INTERPRETER_ROLE_INSTRUCTION = """You are a specialized clinical psychologist and communication expert trained to interpret patient communication patterns.
        
        Your expertise includes:
        - Recognizing when patients minimize, exaggerate, or withhold information
        - Understanding cultural and psychological factors affecting patient communication
        - Translating patient language into objective clinical descriptions
        - Identifying implicit symptoms and concerns not directly stated
        
        You use systematic Chain of Thought reasoning to analyze patient communication step-by-step.
        You help extract the true clinical picture from biased or incomplete patient presentations."""

PATIENT_INTERPRETATION_PROMPT = """
        TASK: Use Chain of Thought reasoning to analyze this patient's communication pattern and extract the true clinical picture.
        
        DETECTED PATIENT BEHAVIOR: {detected_behavior}
        
        CONVERSATION HISTORY:
        {conversation_history}
        
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

# === Behavior Cue Detector Prompts ===
BEHAVIOR_CUE_DETECTOR_ROLE_INSTRUCTION = """You are a behavioral psychologist specializing in patient communication patterns.
        You're expert at identifying subtle signs of information withholding, symptom minimization, 
        anxiety amplification, and other communication biases that affect clinical assessment.
        
        You use Chain of Thought reasoning to systematically analyze patient behavior patterns."""

BEHAVIOR_CUE_DETECTION_PROMPT = """
    Use Chain of Thought reasoning to analyze these patient responses for detailed behavioral patterns:
    
    RECENT PATIENT RESPONSES:
    {recent_responses}
    
    CONVERSATION CONTEXT:
    {conversation_history}
    
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

# === Unbiased Vignette Summarizer Prompts ===
UNBIASED_VIGNETTE_SUMMARIZER_ROLE_INSTRUCTION = """You are an expert clinical summarizer trained to extract objective clinical information 
        while accounting for patient communication biases and psychological factors.
        
        You excel at:
        - Recognizing when patient reporting may be biased
        - Extracting objective clinical facts from subjective presentations
        - Incorporating communication pattern analysis into clinical summaries
        - Providing balanced, unbiased clinical vignettes"""

UNBIASED_VIGNETTE_GENERATION_PROMPT = """
    TASK: Create an objective, unbiased clinical vignette that accounts for patient communication patterns.
    
    CONVERSATION HISTORY:
    {conversation_history}
    
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

# === Diagnosis Prompt Templates ===
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


# === Treatment Plan Prompt ===
TREATMENT_PLAN_PROMPT = """You are a board-certified clinician with extensive experience in primary care and evidence-based medicine. Based on the final diagnosis, create a comprehensive treatment plan that demonstrates clinical expertise and practical implementation.

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

# === Questioning Doctor Prompts ===
EARLY_EXPLORATION_QUESTIONING_ROLE = """You are conducting the EARLY EXPLORATION phase of the clinical interview. Your primary goals are:

        EXPLORATION OBJECTIVES:
        - Establish therapeutic rapport and trust with the patient
        - Gather comprehensive symptom history using open-ended questions
        - Understand the patient's perspective and chief concerns
        - Explore symptom onset, progression, and associated factors
        - Identify pertinent positives and negatives for broad differential diagnosis
        - Assess functional impact and patient's understanding of their condition

        QUESTIONING STRATEGY:
        - Use primarily open-ended questions that encourage elaboration
        - Follow the patient's natural flow of information while gently guiding
        - Ask "Tell me more about..." and "What else have you noticed..."
        - Explore the patient's own words and descriptions without medical jargon
        - Investigate timeline with questions like "When did this first start?" and "How has it changed?"
        - Assess impact with "How is this affecting your daily life?"
        - Explore patient's concerns: "What worries you most about these symptoms?"

        COMMUNICATION APPROACH:
        - Demonstrate active listening with reflective responses
        - Validate the patient's experience and concerns
        - Use the patient's own language and terminology
        - Avoid leading questions that suggest specific diagnoses
        - Create psychological safety for sensitive topics
        - Show genuine curiosity about the patient's experience

        YOUR NEXT QUESTION SHOULD:
        - Be open-ended and encourage detailed response
        - Build on information already shared
        - Explore a new dimension of their symptoms or experience
        - Help establish trust and rapport
        - Gather information relevant to differential diagnosis formation"""

FOCUSED_CLARIFICATION_QUESTIONING_ROLE = """You are conducting the FOCUSED CLARIFICATION phase of the clinical interview. Your primary goals are:

        CLARIFICATION OBJECTIVES:
        - Refine and narrow the differential diagnosis based on emerging patterns
        - Gather specific details about key symptoms that distinguish between diagnoses
        - Explore pertinent review of systems for the developing differential
        - Clarify timeline, triggers, and modifying factors
        - Assess severity and functional impact more precisely
        - Investigate risk factors and family history relevant to suspected conditions

        QUESTIONING STRATEGY:
        - Ask more targeted questions while remaining patient-centered
        - Use specific follow-up questions about previously mentioned symptoms
        - Explore diagnostic criteria for conditions in your differential
        - Ask about associated symptoms that support or refute specific diagnoses
        - Investigate quality, quantity, timing, and context of symptoms
        - Explore what makes symptoms better or worse
        - Ask about previous similar episodes or family history

        COMMUNICATION APPROACH:
        - Balance focused questioning with continued rapport building
        - Acknowledge patient's previous responses to show you're listening
        - Use transitional phrases like "You mentioned X, can you tell me more about..."
        - Be sensitive to patient's communication style and emotional state
        - Clarify patient's terminology to ensure mutual understanding
        - Remain non-judgmental while gathering potentially sensitive information

        DIAGNOSTIC TESTING CONSIDERATION:
        In this focused clarification phase, you should systematically evaluate whether diagnostic testing may be more efficient than continued questioning:

        CLINICAL DECISION FRAMEWORK:
        - Assess if key differential diagnoses require objective data for confirmation/exclusion
        - Evaluate whether continued questioning alone can reasonably narrow the differential
        - Consider if certain conditions in your differential have specific diagnostic tests that would be definitive
        - Determine if patient safety requires urgent testing to rule out serious conditions
        - Balance the efficiency of testing vs additional history-taking

        DIAGNOSTIC TEST CATEGORIES TO CONSIDER:

        BLOOD TESTS - Consider when:
        - Inflammatory conditions require CBC, ESR, CRP confirmation
        - Metabolic disorders need chemistry panels, glucose, electrolytes
        - Infectious causes require blood cultures, specific serologies
        - Autoimmune conditions need ANA, specific antibodies
        - Cardiac conditions require troponins, BNP, lipid panels
        - Endocrine disorders need hormone levels (TSH, cortisol, etc.)

        IMAGING STUDIES - Consider when:
        - Structural abnormalities suspected (X-rays, CT, MRI)
        - Organ-specific visualization needed (ultrasound for gallbladder, echocardiogram for heart)
        - Vascular pathology suspected (Doppler studies, angiography)
        - Emergency conditions require immediate imaging (stroke, pulmonary embolism)

        MICROBIOLOGY - Consider when:
        - Infectious etiology is prominent in differential
        - Antibiotic selection requires culture and sensitivity
        - Specific pathogens need targeted testing (TB, parasites, viruses)
        - Source control needed for treatment planning

        TISSUE SAMPLING/BIOPSY - Consider when:
        - Malignancy is in differential diagnosis
        - Inflammatory conditions require histologic confirmation
        - Skin lesions need pathologic evaluation
        - Lymph node enlargement requires tissue diagnosis

        FUNCTIONAL TESTS - Consider when:
        - Cardiac function assessment needed (ECG, stress testing, echocardiogram)
        - Pulmonary function requires spirometry or exercise testing
        - Neurologic function needs EEG, EMG, or cognitive testing
        - GI function requires endoscopy or motility studies

        GENETIC TESTING - Consider when:
        - Family history suggests hereditary conditions
        - Early-onset diseases suggest genetic etiology
        - Treatment selection depends on genetic markers
        - Rare syndromes are in differential diagnosis

        TESTING vs QUESTIONING DECISION PROCESS:
        You must systematically evaluate:
        1. Can the most likely diagnoses be confirmed/excluded with available history alone?
        2. Would specific tests provide definitive diagnostic information?
        3. Are there serious conditions that require urgent testing for patient safety?
        4. Would testing be more efficient than extensive additional questioning?
        5. Does the patient's presentation warrant immediate objective data?

        YOUR APPROACH IN THIS PHASE SHOULD:
        - First assess whether diagnostic testing is warranted based on current differential
        - If testing is indicated, select the most appropriate and efficient tests
        - If continuing with questions, target specific symptom characteristics or associated findings
        - Help distinguish between competing diagnoses in your differential
        - Explore risk factors or family history relevant to suspected conditions
        - Clarify timeline or progression patterns
        - Assess severity or functional impact more precisely
        - Address any gaps in the clinical picture

        DECISION PRIORITY:
        In the focused clarification phase, lean toward diagnostic testing when:
        - Multiple serious conditions remain in differential that require objective confirmation
        - Patient safety demands urgent rule-out of critical diagnoses
        - Specific tests would be definitive for top differential diagnoses
        - Further questioning is unlikely to significantly narrow the differential
        - Time efficiency favors testing over extensive additional history"""

DIAGNOSTIC_CONFIRMATION_QUESTIONING_ROLE = """You are conducting the DIAGNOSTIC CONFIRMATION phase of the clinical interview. Your primary goals are:

        CONFIRMATION OBJECTIVES:
        - Confirm or refute the most likely diagnosis through targeted questioning
        - Gather final pieces of information needed for diagnostic certainty
        - Assess readiness for treatment discussion and patient education
        - Explore patient's understanding and concerns about the likely diagnosis
        - Investigate any remaining red flags or alternative explanations
        - Prepare for shared decision-making about management options

        QUESTIONING STRATEGY:
        - Ask highly focused questions that address remaining diagnostic uncertainty
        - Explore specific diagnostic criteria for the most likely condition
        - Investigate any concerning features that might change management
        - Ask about patient's previous experiences with similar conditions
        - Explore patient's expectations and concerns about potential diagnosis
        - Assess patient's readiness to discuss treatment options
        - Investigate practical factors that might affect treatment (allergies, medications, lifestyle)

        COMMUNICATION APPROACH:
        - Begin transitioning toward diagnostic discussion and patient education
        - Use more collaborative language: "Based on what you've told me..."
        - Prepare the patient for potential diagnosis without premature closure
        - Address any anxiety or concerns about the diagnostic process
        - Ensure patient feels heard and understood before moving to treatment
        - Set the stage for shared decision-making

        YOUR NEXT QUESTION SHOULD:
        - Address any remaining diagnostic uncertainty
        - Confirm key diagnostic criteria for the most likely condition
        - Explore patient's understanding or concerns about their condition
        - Investigate practical factors relevant to treatment planning
        - Assess patient's readiness for diagnostic and treatment discussion
        - Gather final information needed before diagnostic closure

        DIAGNOSTIC TRANSITION CONSIDERATIONS:
        - If diagnostic certainty is high, begin preparing patient for treatment discussion
        - If uncertainty remains, focus questions on distinguishing features
        - Consider patient's emotional readiness for diagnosis and treatment planning
        - Ensure all critical information is gathered before moving to management phase"""

MODIFIED_QUESTION_GENERATION_PROMPT = """Previously asked questions: {previous_questions}

CLINICAL CONTEXT:
Current interview phase: {interview_phase}

YOUR TASK:
Decide whether to ask a clarifying question OR request a diagnostic test.
Base your decision on the "TESTING vs QUESTIONING DECISION PROCESS" provided in your role.

YOU MUST RESPOND IN THE FOLLOWING FORMAT:

THINKING: 
Use systematic reasoning for your decision:

CLINICAL REASONING:
- Information gaps: <what key information is missing for diagnosis>
- Diagnostic priorities: <which conditions need to be explored or ruled out>
- Testing vs Questioning: <your reasoning for choosing to test or question, based on efficiency, safety, and diagnostic clarity>
- Selected Test (if any): <which test you chose and why it's the most appropriate>
- Question Strategy (if not testing): <what type of question you'll ask and why>

ANSWER:
TEST_REQUEST: <Yes/No>
REQUESTED_TEST: <Name of test if TEST_REQUEST is Yes, otherwise "None">
QUESTION: <Your carefully crafted diagnostic question if TEST_REQUEST is No, otherwise a brief sentence to explain the test to the patient, e.g., "I'd like to order a blood test to get a better look at what's going on.">

CURRENT CLINICAL PICTURE:
Vignette: {vignette_summary}

Leading Diagnoses: {diagnosis}

Patient Communication Pattern: {behavioral_analysis}

Turn Count: {turn_count}
"""

# === Patient Prompts ===
INITIAL_PATIENT_RESPONSE_PROMPT = """{patient_instructions}

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

FOLLOWUP_PATIENT_RESPONSE_PROMPT = """{patient_followup_instructions}

You are a real patient responding to your doctor. Be authentic to your behavioral type: {behavior_type}.

YOU MUST RESPOND IN THE FOLLOWING FORMAT:

THINKING: Think about how you feel about your symptoms and this doctor's question. Consider your emotions, confusion, and how you naturally communicate as a {behavior_type} patient.

ANSWER: Give your natural, realistic patient response in your own words (NOT medical terminology).

CONTEXT:
- Your symptoms: {vignette_text}
- Doctor asked: {followup_question}
- Your behavior type: {behavior_type}
- Response style: {response_guidance}

Remember: You are NOT trying to be a good patient or help the doctor. You're being a REAL person with real concerns, confusion, and communication patterns."""

BASE_PATIENT_INSTRUCTIONS = """You are simulating a real patient in conversation with their doctor. 
Respond naturally and realistically, as if you are experiencing symptoms yourself — but like a real patient, you are NOT medically trained and do NOT understand what's important or what anything means. 
You have NOT spoken to any other doctors. 
You may feel scared, unsure, or even embarrassed. 
You are NOT trying to impress the doctor with a clear answer — just describe what you feel in your own confused way."""

# === Test Result Generation Prompts ===
TEST_RESULT_GENERATOR_ROLE = """You are a medical laboratory system that generates realistic test results based on clinical scenarios.

You have access to comprehensive medical knowledge and can generate appropriate test results that would be consistent with various diagnoses.

You generate results that are:
- Medically accurate and realistic
- Appropriately formatted as professional lab/imaging reports
- Consistent with the clinical picture and gold diagnosis
- Include normal reference ranges where applicable
- Reflect what would actually be found in real patients with this condition"""

TEST_RESULT_GENERATION_PROMPT = """
TASK: Generate realistic test results for the requested test based on the clinical scenario.

CLINICAL CONTEXT:
Gold Diagnosis: {gold_diagnosis}
Current Vignette: {current_vignette}
Requested Test: {requested_test}

INSTRUCTIONS:
1. Generate results that would be consistent with the gold diagnosis
2. Format as a professional laboratory/imaging report
3. Include appropriate reference ranges and units
4. Make results realistic and medically accurate
5. Include relevant abnormal findings that support the diagnosis
6. Format as if coming from a hospital lab/radiology department

RESPOND IN THIS FORMAT:

THINKING:
- What test was requested: <identify the specific test>
- Expected findings for {gold_diagnosis}: <what results should show>
- Normal vs abnormal values: <what should be abnormal to support diagnosis>
- Report formatting: <how this type of test result is typically presented>

ANSWER:
[Professional lab/imaging report format with header, patient info placeholder, test results, and appropriate medical formatting]
"""

VIGNETTE_UPDATE_WITH_TEST_RESULTS_PROMPT = """
        TASK: Update the clinical vignette to incorporate new objective test results.
        
        CONVERSATION HISTORY:
        {conversation_history}
        
        PREVIOUS VIGNETTE:
        {previous_vignette}
        
        INSTRUCTIONS:
        1. The latest patient response contains objective test results
        2. Incorporate these results into the clinical picture
        3. Maintain the existing clinical narrative while adding test findings
        4. Format as a comprehensive clinical vignette
        
        RESPOND IN THIS FORMAT:
        
        THINKING:
        <Analysis of how the test results update the clinical picture>
        
        ANSWER: <Updated clinical vignette incorporating test results>
        """

def generate_patient_prompt_modifiers(behavior_config, is_initial=True):
    """Generate prompt modifiers based on selected patient behavior"""
    modifiers = behavior_config.get("modifiers", [])

    base_instructions = BASE_PATIENT_INSTRUCTIONS

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
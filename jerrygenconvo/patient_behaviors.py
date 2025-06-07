# patient_behaviors.py
"""
Patient behavior configurations and generators for the medical simulation system.
"""

import random

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
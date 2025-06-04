# agents.py
"""
Specialized agent classes for the medical diagnosis simulation system.
"""

import json
from role_responder import RoleResponder
from prompts import (
    PATIENT_INTERPRETER_PROMPT,
    BEHAVIORAL_ANALYSIS_PROMPT,
    UNBIASED_VIGNETTE_PROMPT,
    EARLY_DIAGNOSIS_PROMPT,
    MIDDLE_DIAGNOSIS_PROMPT,
    LATE_DIAGNOSIS_PROMPT,
    EARLY_QUESTIONING_ROLE,
    MIDDLE_QUESTIONING_ROLE,
    LATE_QUESTIONING_ROLE,
    QUESTIONING_PROMPT,
)


class PatientInterpreter:
    """Agent specialized in reading patient communication patterns and extracting unbiased clinical information using Chain of Thought reasoning"""

    def __init__(self, client, model):
        self.role_instruction = """You are a specialized clinical psychologist and communication expert trained to interpret patient communication patterns.
        
        Your expertise includes:
        - Recognizing when patients minimize, exaggerate, or withhold information
        - Understanding cultural and psychological factors affecting patient communication
        - Translating patient language into objective clinical descriptions
        - Identifying implicit symptoms and concerns not directly stated
        
        You use systematic Chain of Thought reasoning to analyze patient communication step-by-step.
        You help extract the true clinical picture from biased or incomplete patient presentations."""

        self.responder = RoleResponder(self.role_instruction, client, model)

    def interpret_patient_communication(
        self, conversation_history, detected_behavior, current_vignette
    ):
        """Analyze patient communication to extract unbiased clinical information using Chain of Thought reasoning"""

        interpretation_prompt = PATIENT_INTERPRETER_PROMPT.format(
            detected_behavior=detected_behavior,
            conversation_history=json.dumps(conversation_history[-6:], indent=2),  # Last 6 exchanges
            current_vignette=current_vignette
        )

        return self.responder.ask(interpretation_prompt)


class BehaviorAnalyzer:
    """Agent that detects patient behavioral patterns and communication cues"""
    
    def __init__(self, client, model):
        self.role_instruction = """You are a behavioral psychologist specializing in patient communication patterns.
        You're expert at identifying subtle signs of information withholding, symptom minimization, 
        anxiety amplification, and other communication biases that affect clinical assessment.
        
        You use Chain of Thought reasoning to systematically analyze patient behavior patterns."""
        
        self.responder = RoleResponder(self.role_instruction, client, model)
    
    def detect_patient_behavior_cues(self, conversation_history, patient_responses):
        """Enhanced version that provides more detailed behavioral analysis using Chain of Thought reasoning"""
        recent_responses = patient_responses[-3:]

        analysis_prompt = BEHAVIORAL_ANALYSIS_PROMPT.format(
            recent_responses=json.dumps(recent_responses, indent=2),
            conversation_context=json.dumps(conversation_history[-6:], indent=2)
        )

        return self.responder.ask(analysis_prompt)


class ClinicalSummarizer:
    """Agent that creates unbiased clinical vignettes from patient conversations"""
    
    def __init__(self, client, model):
        self.role_instruction = """You are an expert clinical summarizer trained to extract objective clinical information 
        while accounting for patient communication biases and psychological factors.
        
        You excel at:
        - Recognizing when patient reporting may be biased
        - Extracting objective clinical facts from subjective presentations
        - Incorporating communication pattern analysis into clinical summaries
        - Providing balanced, unbiased clinical vignettes"""
        
        self.responder = RoleResponder(self.role_instruction, client, model)
    
    def generate_unbiased_vignette(self, conversation_history, previous_vignette, patient_interpretation):
        """Generate a vignette that accounts for patient communication biases"""
        
        summary_prompt = UNBIASED_VIGNETTE_PROMPT.format(
            conversation_history=json.dumps(conversation_history, indent=2),
            previous_vignette=previous_vignette,
            patient_interpretation=patient_interpretation
        )

        return self.responder.ask(summary_prompt)


class DiagnosticsExpert:
    """Agent specialized in medical diagnosis with stage-based reasoning"""
    
    def __init__(self, client, model):
        self.role_instruction = "You are a board-certified diagnostician."
        self.responder = RoleResponder(self.role_instruction, client, model)
    
    def get_diagnosis_response(self, turn_count, gold_label, vignette_summary, previous_questions):
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
        response = self.responder.ask(
            base_prompt.format(
                prev_questions=json.dumps(previous_questions),
                vignette=vignette_summary,
                turn_count=turn_count,
            )
        )

        return response, stage


class ClinicalQuestioner:
    """Agent that asks diagnostic questions based on interview phase"""
    
    def __init__(self, client, model):
        self.client = client
        self.model = model
    
    def generate_question(self, turn_count, previous_questions, vignette_summary, 
                         diagnosis, behavioral_analysis, gold_label):
        """Generate appropriate diagnostic question based on interview phase"""
        
        # Determine phase and base role
        if turn_count < 4:
            base_questioning_role = EARLY_QUESTIONING_ROLE
            phase = "EARLY EXPLORATION"
        elif turn_count >= 4 and turn_count < 8:
            base_questioning_role = MIDDLE_QUESTIONING_ROLE
            phase = "FOCUSED CLARIFICATION"
        else:
            base_questioning_role = LATE_QUESTIONING_ROLE
            phase = "DIAGNOSTIC CONFIRMATION"
        
        # Add gold diagnosis guidance to questioning (if needed)
        # For now, we'll use the base role as-is
        guided_questioning_role = base_questioning_role
        
        # Create questioner with enhanced role definition
        questioner = RoleResponder(guided_questioning_role, self.client, self.model)
        
        prompt = QUESTIONING_PROMPT.format(
            previous_questions=json.dumps(previous_questions),
            phase=phase,
            vignette_summary=vignette_summary,
            diagnosis=diagnosis,
            behavioral_analysis=behavioral_analysis,
            turn_count=turn_count
        )
        
        return questioner.ask(prompt)
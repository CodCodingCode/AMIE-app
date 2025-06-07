# agents.py
"""
Specialized agent classes for the medical diagnosis simulation system.
"""

import json
import os
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Optional, Any
from openai import OpenAI
from role_responder import RoleResponder
from prompts import (
    PATIENT_INTERPRETER_PROMPT,
    BEHAVIORAL_ANALYSIS_PROMPT,
    UNBIASED_VIGNETTE_PROMPT,
    EARLY_QUESTIONING_ROLE,
    MIDDLE_QUESTIONING_ROLE,
    LATE_QUESTIONING_ROLE,
    QUESTIONING_PROMPT,
)

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

DATABASE CONTEXT:
The following diseases have been identified as potentially relevant based on semantic similarity to the patient's presentation. Consider these as reference material to inform your differential diagnosis, but use your clinical judgment to determine their actual relevance:

{disease_summaries}

Turn count: {turn_count}

CRITICAL: You must respond ONLY in the exact format below. Do not add any notes, recommendations, further evaluations, or additional text after the ANSWER section.

THINKING:
Use systematic diagnostic reasoning:
- Patient demographics: <age, gender, relevant social factors>
- Key presenting symptoms: <primary and secondary symptoms>
- Symptom characteristics: <onset, duration, quality, severity, triggers, relieving factors>
- Associated symptoms: <related findings that support or refute diagnoses>
- Clinical context: <relevant history, risk factors, red flags>
- Database insights: <how the retrieved diseases inform my thinking>
- Diagnostic approach: <what clinical reasoning guides my differential>
- Probability assessment: <which diagnoses are most vs least likely and why>
- Make sure to ONLY use the information provided in the vignette, previous questions, and database context

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

DATABASE CONTEXT:
The following diseases have been identified as potentially relevant based on semantic similarity to the patient's presentation. Use these to inform your refined differential diagnosis:

{disease_summaries}

Turn count: {turn_count}

CRITICAL: You must respond ONLY in the exact format below. Do not add any notes, recommendations, or additional text after the ANSWER section.

THINKING:
Apply focused diagnostic reasoning:
- Symptom evolution: <how symptoms have been clarified or evolved through questioning>
- Key clinical findings: <most important positive and negative findings>
- Pattern recognition: <what clinical syndrome/pattern emerges>
- Discriminating features: <findings that help distinguish between competing diagnoses>
- Database insights: <how the retrieved diseases inform my refined thinking>
- Probability refinement: <how additional information changes diagnostic likelihood>
- Risk stratification: <which diagnoses pose immediate vs long-term risk>
- Clinical coherence: <which diagnoses best explain the complete clinical picture>
- Make sure to ONLY use the information provided in the vignette, previous questions, and database context

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

DATABASE CONTEXT:
The following diseases have been identified as potentially relevant based on semantic similarity to the patient's presentation. Use these to inform your final diagnostic assessment:

{disease_summaries}

CRITICAL: You must respond ONLY in the exact format below. Do not add any notes, recommendations, or additional text.

THINKING:
Apply diagnostic closure reasoning:

CLINICAL SYNTHESIS:
- Complete symptom profile: <comprehensive review of all reported symptoms>
- Timeline and progression: <how symptoms developed and evolved>
- Clinical pattern recognition: <what syndrome/condition this represents>
- Supporting evidence: <specific findings that confirm the diagnosis>
- Database insights: <how the retrieved diseases inform my final assessment>
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
            conversation_history=json.dumps(conversation_history[-6:], indent=2),
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
    """Agent specialized in medical diagnosis with stage-based reasoning and integrated disease retrieval"""
    
    def __init__(self, client, model, disease_db_path: str = "results.json", 
                 embedding_model: str = "text-embedding-3-small", 
                 cache_path: str = "disease_embeddings.json"):
        self.role_instruction = "You are a board-certified diagnostician."
        self.responder = RoleResponder(self.role_instruction, client, model)
        self.client = client
        self.embedding_model = embedding_model
        self.cache_path = cache_path
        
        with open(disease_db_path, 'r') as f:
            disease_data = json.load(f)
        
        self.disease_db = self._convert_to_dict(disease_data)
        self.disease_embeddings = self._load_or_generate_embeddings()
    
    def _convert_to_dict(self, disease_list: List[Dict]) -> Dict[str, Dict]:
        """Convert disease list to dictionary keyed by disease name"""
        return {disease['disease_name']: disease for disease in disease_list}

    def _embed(self, text: str) -> List[float]:
        """Generate embeddings for text using OpenAI API"""
        response = self.client.embeddings.create(
            input=text,
            model=self.embedding_model
        )
        return response.data[0].embedding

    def _construct_embedding_text(self, info: Dict) -> str:
        """Construct text for embedding from disease info"""
        parts = []
        
        list_fields = ["symptoms", "causes", "risk_factors", "hereditary_factors"]
        for field in list_fields:
            if field in info and isinstance(info[field], list):
                parts.extend(info[field])
        
        if "family_history_impact" in info and isinstance(info["family_history_impact"], dict):
            fh_impact = info["family_history_impact"]
            for key, value in fh_impact.items():
                if isinstance(value, str):
                    parts.append(f"{key}: {value}")
        
        string_fields = ["genetic_risk_assessment"]
        for field in string_fields:
            if field in info and isinstance(info[field], str):
                parts.append(info[field])
        
        return " ".join(parts)

    def _generate_cache_key(self, disease_name: str, embed_text: str) -> str:
        """Generate a stable cache key"""
        import hashlib
        text_hash = hashlib.md5(embed_text.encode()).hexdigest()
        return f"{disease_name}_{text_hash}"

    def _load_or_generate_embeddings(self) -> Dict[str, List[float]]:
        """Load cached embeddings or generate new ones"""
        if os.path.exists(self.cache_path):
            with open(self.cache_path, "r") as f:
                cached = json.load(f)
        else:
            cached = {}

        updated = False
        disease_embeddings = {}
        
        for disease_name, info in self.disease_db.items():
            embed_text = self._construct_embedding_text(info)
            cache_key = self._generate_cache_key(disease_name, embed_text)

            if cache_key not in cached:
                embedding = self._embed(embed_text)
                cached[cache_key] = embedding
                updated = True

            disease_embeddings[disease_name] = cached[cache_key]

        if updated:
            with open(self.cache_path, "w") as f:
                json.dump(cached, f, indent=2)

        return disease_embeddings

    def _generate_similarity_explanation(self, patient_info: str, disease_name: str, disease_info: Dict) -> str:
        """Generate explanation for why a disease is similar to patient presentation"""
        
        disease_summary_parts = []
        if "symptoms" in disease_info and disease_info["symptoms"]:
            disease_summary_parts.append(f"Symptoms: {', '.join(disease_info['symptoms'][:5])}")
        if "causes" in disease_info and disease_info["causes"]:
            disease_summary_parts.append(f"Causes: {', '.join(disease_info['causes'][:3])}")
        if "risk_factors" in disease_info and disease_info["risk_factors"]:
            disease_summary_parts.append(f"Risk factors: {', '.join(disease_info['risk_factors'][:3])}")
        
        disease_summary = "; ".join(disease_summary_parts)
        
        system_prompt = """You are a medical assistant. Compare a patient's presentation with a disease profile and explain why they are similar. 

Provide a concise explanation (1-2 sentences) focusing on the most relevant matching aspects like symptoms, risk factors, or causes. Be specific and medical in your language.

Format: "Similar because [specific matching elements]."
"""

        user_prompt = f"""Patient presentation: {patient_info}

Disease: {disease_name}
Disease profile: {disease_summary}

Explain why this disease is similar to the patient's presentation:"""

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2,
            max_tokens=150
        )
        
        return response.choices[0].message.content.strip()

    def _parse_patient_summary(self, patient_text: str) -> Dict[str, List[str]]:
        """Parse patient summary text and extract structured information"""
        system_prompt = """You are a medical text parser. Extract and categorize information from patient summaries into these specific categories:

1. symptoms: Physical signs, complaints, and manifestations (e.g., "redness", "swelling", "discharge", "pain")
2. causes: Potential underlying causes or triggers mentioned (e.g., "infection", "exposure", "trauma")
3. risk_factors: Environmental, behavioral, or situational factors (e.g., "close contact", "recent travel", "immunocompromised")
4. family_history_impact: Family history or hereditary concerns mentioned (e.g., "family history of", "genetic predisposition")
5. hereditary_factors: Genetic or inherited conditions specifically mentioned

Return ONLY a valid JSON object with these exact keys. Each value should be a list of strings. Use clear, concise medical terms. If a category has no relevant information, use an empty list.

Example format:
{
    "symptoms": ["eye redness", "swelling", "discharge", "light sensitivity"],
    "causes": ["possible infection"],
    "risk_factors": ["recent onset", "ocular exposure"],
    "family_history_impact": [],
    "hereditary_factors": []
}"""

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Parse this patient summary:\n\n{patient_text}"}
            ],
            temperature=0.1,
            max_tokens=800
        )
        
        result_text = response.choices[0].message.content.strip()
        
        if result_text.startswith('```json'):
            result_text = result_text[7:-3].strip()
        elif result_text.startswith('```'):
            result_text = result_text[3:-3].strip()
        
        parsed_data = json.loads(result_text)
        
        for key in ["symptoms", "causes", "risk_factors", "family_history_impact", "hereditary_factors"]:
            if not isinstance(parsed_data[key], list):
                parsed_data[key] = []
        
        return parsed_data

    def _get_relevant_diseases_from_text(self, patient_text: str, top_k: int = 10, include_explanations: bool = True) -> List[Dict[str, Any]]:
        """Get relevant diseases directly from patient summary text as structured data"""
        parsed_info = self._parse_patient_summary(patient_text)
        diseases_result = self._get_relevant_diseases(
            symptoms=parsed_info["symptoms"],
            causes=parsed_info["causes"],
            risk_factors=parsed_info["risk_factors"],
            family_history_impact=parsed_info["family_history_impact"],
            hereditary_factors=parsed_info["hereditary_factors"],
            top_k=top_k,
            include_explanations=include_explanations,
            original_patient_text=patient_text
        )
        
        return diseases_result

    def _get_relevant_diseases(
        self, 
        symptoms: Optional[List[str]] = None, 
        causes: Optional[List[str]] = None, 
        risk_factors: Optional[List[str]] = None, 
        family_history_impact: Optional[List[str]] = None, 
        hereditary_factors: Optional[List[str]] = None,
        top_k: int = 10,
        include_explanations: bool = True,
        original_patient_text: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get diseases relevant to given symptoms and factors with explanations"""
        input_parts = []
        
        for parts_list in [symptoms, causes, risk_factors, family_history_impact, hereditary_factors]:
            if parts_list:
                input_parts.extend(parts_list)
        
        input_text = " ".join(input_parts)
        input_embedding = np.array(self._embed(input_text)).reshape(1, -1)

        similarities = []
        for disease_name, emb in self.disease_embeddings.items():
            emb_array = np.array(emb).reshape(1, -1)
            score = cosine_similarity(input_embedding, emb_array)[0][0]
            similarities.append((disease_name, score, self.disease_db[disease_name]))

        top_matches = sorted(similarities, key=lambda x: x[1], reverse=True)[:top_k]
        
        results = []
        patient_context = original_patient_text or input_text
        
        for disease_name, score, info in top_matches:
            result = {
                "disease_name": disease_name,
                "similarity_score": round(float(score), 4),
                "disease_info": {
                    "symptoms": info.get("symptoms", []),
                    "causes": info.get("causes", []),
                    "risk_factors": info.get("risk_factors", []),
                    "prognosis": info.get("prognosis", ""),
                    "hereditary_factors": info.get("hereditary_factors", []),
                    "family_history_impact": info.get("family_history_impact", {}),
                    "genetic_risk_assessment": info.get("genetic_risk_assessment", "")
                }
            }
            
            if include_explanations:
                explanation = self._generate_similarity_explanation(
                    patient_context, disease_name, info
                )
                result["similarity_explanation"] = explanation
            
            results.append(result)
        
        return results
    
    def _format_disease_context_comprehensive(self, disease_data_list):
        """Format complete disease data into comprehensive string for prompt context"""
        output_sections = []
        
        for i, disease in enumerate(disease_data_list, 1):
            disease_section = f"=== Disease {i}: {disease['disease_name']} ===\n"
            disease_section += f"Similarity Score: {disease['similarity_score']}\n"
            disease_section += f"Similarity Explanation: {disease['similarity_explanation']}\n\n"
            
            disease_info = disease['disease_info']
            
            if disease_info['symptoms']:
                disease_section += f"Symptoms: {', '.join(disease_info['symptoms'])}\n"
            
            if disease_info['causes']:
                disease_section += f"Causes: {', '.join(disease_info['causes'])}\n"
            
            if disease_info['risk_factors']:
                disease_section += f"Risk Factors: {', '.join(disease_info['risk_factors'])}\n"
            
            if disease_info['hereditary_factors']:
                disease_section += f"Hereditary Factors: {', '.join(disease_info['hereditary_factors'])}\n"
            
            if disease_info['family_history_impact']:
                fh_impact = disease_info['family_history_impact']
                if isinstance(fh_impact, dict):
                    fh_parts = []
                    for key, value in fh_impact.items():
                        fh_parts.append(f"{key}: {value}")
                    disease_section += f"Family History Impact: {'; '.join(fh_parts)}\n"
                else:
                    disease_section += f"Family History Impact: {fh_impact}\n"
            
            if disease_info['genetic_risk_assessment']:
                disease_section += f"Genetic Risk Assessment: {disease_info['genetic_risk_assessment']}\n"
            
            if disease_info['prognosis']:
                disease_section += f"Prognosis: {disease_info['prognosis']}\n"
            
            output_sections.append(disease_section)
        
        return "\n".join(output_sections)
    
    def _format_disease_context_concise(self, disease_data_list):
        """Format disease data into concise string for prompt context"""
        output_lines = []
        for i, disease in enumerate(disease_data_list, 1):
            disease_info = disease['disease_info']
            
            summary_parts = []
            
            if disease_info['symptoms']:
                symptoms_str = ', '.join(disease_info['symptoms'][:5])
                if len(disease_info['symptoms']) > 5:
                    symptoms_str += f" (+{len(disease_info['symptoms'])-5} more)"
                summary_parts.append(f"Symptoms: [{symptoms_str}]")
            
            if disease_info['causes']:
                causes_str = ', '.join(disease_info['causes'][:3])
                if len(disease_info['causes']) > 3:
                    causes_str += f" (+{len(disease_info['causes'])-3} more)"
                summary_parts.append(f"Causes: [{causes_str}]")
            
            if disease_info['risk_factors']:
                rf_str = ', '.join(disease_info['risk_factors'][:3])
                if len(disease_info['risk_factors']) > 3:
                    rf_str += f" (+{len(disease_info['risk_factors'])-3} more)"
                summary_parts.append(f"Risk Factors: [{rf_str}]")
            
            if disease_info['prognosis']:
                prognosis = disease_info['prognosis']
                if len(prognosis) > 100:
                    prognosis = prognosis[:97] + "..."
                summary_parts.append(f"Prognosis: [{prognosis}]")
            
            disease_summary = f"Disease: {disease['disease_name']} (Score: {disease['similarity_score']}) - {disease['similarity_explanation']}\n"
            disease_summary += " | ".join(summary_parts)
            
            output_lines.append(disease_summary)
        
        return "\n\n".join(output_lines)
    
    def _format_disease_context_structured(self, disease_data_list):
        """Format disease data into structured JSON-like string for prompt context"""
        formatted_diseases = []
        
        for disease in disease_data_list:
            structured_disease = {
                "name": disease['disease_name'],
                "similarity": {
                    "score": disease['similarity_score'],
                    "explanation": disease['similarity_explanation']
                },
                "clinical_profile": {
                    "symptoms": disease['disease_info']['symptoms'],
                    "causes": disease['disease_info']['causes'],
                    "risk_factors": disease['disease_info']['risk_factors'],
                    "hereditary_factors": disease['disease_info']['hereditary_factors'],
                    "family_history_impact": disease['disease_info']['family_history_impact'],
                    "genetic_risk_assessment": disease['disease_info']['genetic_risk_assessment'],
                    "prognosis": disease['disease_info']['prognosis']
                }
            }
            formatted_diseases.append(structured_disease)
        
        return json.dumps(formatted_diseases, indent=2)
    
    def get_diagnosis_response(self, turn_count, gold_label, vignette_summary, previous_questions, formatting_style="comprehensive"):
        """Get diagnosis with proper stage-based prompting and flexible formatting"""
        if turn_count < 4:
            base_prompt = EARLY_DIAGNOSIS_PROMPT
            stage = "early"
        elif turn_count >= 4 and turn_count < 8:
            base_prompt = MIDDLE_DIAGNOSIS_PROMPT
            stage = "middle"
        else:
            base_prompt = LATE_DIAGNOSIS_PROMPT
            stage = "late"

        disease_data = self._get_relevant_diseases_from_text(vignette_summary, top_k=10)
        
        if formatting_style == "comprehensive":
            disease_context = self._format_disease_context_comprehensive(disease_data)
        elif formatting_style == "concise":
            disease_context = self._format_disease_context_concise(disease_data)
        elif formatting_style == "structured":
            disease_context = self._format_disease_context_structured(disease_data)
        else:
            disease_context = self._format_disease_context_comprehensive(disease_data)

        response = self.responder.ask(
            base_prompt.format(
                prev_questions=json.dumps(previous_questions),
                vignette=vignette_summary,
                disease_summaries=disease_context,
                turn_count=turn_count,
            )
        )

        return response, stage, disease_data


class ClinicalQuestioner:
    """Agent that asks diagnostic questions based on interview phase"""
    
    def __init__(self, client, model):
        self.client = client
        self.model = model
    
    def _format_disease_context_for_questioning(self, disease_data_list):
        """Format disease data into a string context for questioning guidance"""
        context_lines = []
        context_lines.append("DISEASE CONTEXT FOR QUESTIONING:")
        context_lines.append("These are diseases that show similarity to the patient's presentation. Use the information from these diseases to guide your questioning and explore relevant symptom patterns, risk factors, and clinical features.")
        context_lines.append("")
        
        for i, disease in enumerate(disease_data_list, 1):
            disease_info = disease['disease_info']
            
            disease_parts = []
            disease_parts.append(f"Disease Name: {disease['disease_name']}")
            
            if disease_info['symptoms']:
                disease_parts.append(f"Symptoms: {', '.join(disease_info['symptoms'])}")
            
            if disease_info['causes']:
                disease_parts.append(f"Causes: {', '.join(disease_info['causes'])}")
            
            if disease_info['risk_factors']:
                disease_parts.append(f"Risk Factors: {', '.join(disease_info['risk_factors'])}")
            
            if disease_info['hereditary_factors']:
                disease_parts.append(f"Hereditary Factors: {', '.join(disease_info['hereditary_factors'])}")
            
            if disease_info['family_history_impact']:
                fh_impact = disease_info['family_history_impact']
                if isinstance(fh_impact, dict):
                    fh_parts = []
                    for key, value in fh_impact.items():
                        fh_parts.append(f"{key}: {value}")
                    disease_parts.append(f"Family History Impact: {'; '.join(fh_parts)}")
                else:
                    disease_parts.append(f"Family History Impact: {fh_impact}")
            
            if disease_info['genetic_risk_assessment']:
                disease_parts.append(f"Genetic Risk Assessment: {disease_info['genetic_risk_assessment']}")
            
            disease_parts.append(f"Similarity Score: {disease['similarity_score']}")
            
            disease_string = ", ".join(disease_parts)
            context_lines.append(f"{i}. {disease_string}")
            context_lines.append("")
        
        return "\n".join(context_lines)
    
    def generate_question(self, turn_count, previous_questions, vignette_summary, 
                         diagnosis, behavioral_analysis, gold_label, disease_data=None):
        """Generate appropriate diagnostic question based on interview phase with disease context"""
        
        if turn_count < 4:
            base_questioning_role = EARLY_QUESTIONING_ROLE
            phase = "EARLY EXPLORATION"
        elif turn_count >= 4 and turn_count < 8:
            base_questioning_role = MIDDLE_QUESTIONING_ROLE
            phase = "FOCUSED CLARIFICATION"
        else:
            base_questioning_role = LATE_QUESTIONING_ROLE
            phase = "DIAGNOSTIC CONFIRMATION"
        
        if disease_data:
            disease_context = self._format_disease_context_for_questioning(disease_data)
        else:
            disease_context = "No disease context provided."
        
        enhanced_questioning_role = f"""{base_questioning_role}

{disease_context}

Use the disease context above to inform your questioning strategy. Look for symptoms, risk factors, and clinical features mentioned in similar diseases to guide your inquiry."""
        
        questioner = RoleResponder(enhanced_questioning_role, self.client, self.model)
        
        prompt = QUESTIONING_PROMPT.format(
            previous_questions=json.dumps(previous_questions),
            phase=phase,
            vignette_summary=vignette_summary,
            diagnosis=diagnosis,
            behavioral_analysis=behavioral_analysis,
            turn_count=turn_count
        )
        
        return questioner.ask(prompt)
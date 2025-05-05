import numpy as np
from typing import Dict, List, Tuple
import random
from openai import OpenAI
import os
from api_key import key

# Initialize OpenAI client
API_KEY = key
client = OpenAI(api_key=API_KEY)

def calculate_entropy(probabilities: Dict[str, float]) -> float:
    """Calculate the entropy of a probability distribution."""
    return -sum(p * np.log2(p) for p in probabilities.values() if p > 0)

def generate_questions(patient_info: str, num_questions: int = 20) -> List[str]:
    """Generate relevant diagnostic questions based on patient information."""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": f"""
You are an expert medical diagnostician. Based on the patient information provided, generate {num_questions} highly specific diagnostic questions that would help narrow down the diagnosis.

Patient Information: {patient_info}

Instructions:
1. Generate EXACTLY {num_questions} specific questions a doctor would ask this patient
2. Questions should be phrased to be answerable with Yes, No, or Not Sure
3. Focus on symptoms, risk factors, and relevant medical history
4. Make questions specific and directly relevant to likely diagnoses
5. Vary the questions to cover different body systems and potential diagnoses
6. Each question should be on its own line with no numbering or additional text
7. Questions should help differentiate between the most likely diagnoses
8. Do not include any explanations or additional text
"""}
        ]
    )
    
    questions = [q.strip() for q in response.choices[0].message.content.strip().split('\n') if q.strip()]
    return questions[:num_questions]  # Ensure we have exactly num_questions

def calculate_scenario_probabilities(patient_info: str, question: str) -> Dict[str, float]:
    """Calculate probabilities of different answer scenarios for a given question."""
    print(f"  Calculating scenario probabilities for question: {question}")
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": f"""
You are an expert in medical probability estimation. Given the patient information and a diagnostic question, generate 3 possible responses and their probabilities.

Patient Information: {patient_info}

Question: {question}

Instructions:
1. Generate EXACTLY 3 possible responses to this question
2. Each response should be a natural, patient-like answer
3. Assign a probability to each response
4. Probabilities must sum to exactly 1.0
5. Express each probability as a decimal between 0 and 1
6. Consider the patient's demographics, symptoms, and history
7. Base your estimates on medical knowledge and typical disease presentations
8. Return ONLY the responses and probabilities in this exact format:
Response 1|0.XX
Response 2|0.XX
Response 3|0.XX
"""}
        ]
    )
    
    scenario_probs = {}
    for line in response.choices[0].message.content.strip().split('\n'):
        if '|' in line:
            scenario, prob_str = line.split('|', 1)
            try:
                scenario_probs[scenario.strip()] = float(prob_str.strip())
            except ValueError:
                pass
    
    # Validate and normalize probabilities
    if not scenario_probs or abs(sum(scenario_probs.values()) - 1.0) > 0.01:
        # If probabilities don't sum to ~1, assign equal probabilities
        scenarios = [f"Response {i+1}" for i in range(3)]
        scenario_probs = {scenario: 1.0/3 for scenario in scenarios}
    
    print(f"  Scenario probabilities calculated: {scenario_probs}")
    return scenario_probs

def update_disease_probabilities(patient_info: str, diseases_with_probs: List[Tuple[str, float]], 
                                question: str, answer: str, base_diseases: List[str]) -> Dict[str, float]:
    """Update disease probabilities based on a new question and answer."""
    print(f"  Updating disease probabilities for answer: {answer}")
    diseases_str = "\n".join([f"{disease}|{prob}" for disease, prob in diseases_with_probs])
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": f"""
You are an expert medical diagnosis assistant. Given the patient information, current disease probabilities, and a new question with its answer, update the disease probabilities.

Patient Information: {patient_info}

Base Diseases (these are the only possible diagnoses):
{', '.join(base_diseases)}

Current disease probabilities:
{diseases_str}

New Information:
Question: {question}
Answer: {answer}

Instructions:
1. Consider how the new information impacts each disease probability
2. Update each probability based on medical knowledge
3. The probabilities must sum to exactly 1.0
4. Return only the updated probabilities in this exact format:
Disease name 1|0.XXX
Disease name 2|0.XXX
etc.
5. Only include diseases from the base diseases list
6. Do not include any explanations or additional text
"""}
        ]
    )
    
    updated_probs = {}
    for line in response.choices[0].message.content.strip().split('\n'):
        if '|' in line:
            disease, prob_str = line.split('|', 1)
            try:
                if disease.strip() in base_diseases:  # Only include base diseases
                    updated_probs[disease.strip()] = float(prob_str.strip())
            except ValueError:
                pass
    
    # If we got invalid output, return original probabilities
    if not updated_probs or abs(sum(updated_probs.values()) - 1.0) > 0.01:
        return {disease: prob for disease, prob in diseases_with_probs}
    
    print(f"  Updated probabilities: {updated_probs}")
    return updated_probs

def evaluate_question_info_gain(patient_info: str, question: str, 
                               diseases_with_probs: List[Tuple[str, float]], base_diseases: List[str]) -> float:
    """Calculate information gain for a single question."""
    print(f"  Evaluating information gain for question: {question}")
    # Current entropy
    current_probs = {disease: prob for disease, prob in diseases_with_probs}
    current_entropy = calculate_entropy(current_probs)
    print(f"  Current entropy: {current_entropy:.4f}")
    
    # Calculate scenario probabilities
    scenario_probs = calculate_scenario_probabilities(patient_info, question)
    
    # Calculate expected entropy
    expected_entropy = 0
    for scenario, prob in scenario_probs.items():
        print(f"  Processing scenario: {scenario}")
        # Update probabilities based on scenario
        new_probs = update_disease_probabilities(patient_info, diseases_with_probs, question, scenario, base_diseases)
        
        # Calculate entropy for this scenario
        scenario_entropy = calculate_entropy(new_probs)
        expected_entropy += prob * scenario_entropy
        print(f"  Scenario entropy: {scenario_entropy:.4f}")
    
    # Calculate information gain
    info_gain = current_entropy - expected_entropy
    print(f"  Information gain: {info_gain:.4f}")
    return info_gain

def information_gain_network(patient_info: str, diseases: List[str]) -> str:
    """
    Main function that calculates the question with the highest information gain.
    
    Args:
        patient_info: Patient vignette/information
        diseases: List of possible diseases
        
    Returns:
        The question with the highest information gain
    """
    print("\nStarting information gain network...")
    # Initialize equal probabilities for all diseases
    num_diseases = len(diseases)
    initial_prob = 1.0 / num_diseases
    diseases_with_probs = [(disease, initial_prob) for disease in diseases]
    print(f"Initialized {num_diseases} diseases with equal probabilities")
    
    # Generate questions
    print("Generating questions...")
    questions = generate_questions(patient_info)
    print(f"Generated {len(questions)} questions")
    
    # Evaluate information gain for each question
    print("Evaluating information gain for each question...")
    info_gains = []
    for i, question in enumerate(questions, 1):
        print(f"\nEvaluating question {i}/{len(questions)}")
        try:
            info_gain = evaluate_question_info_gain(patient_info, question, diseases_with_probs, diseases)
            info_gains.append((question, info_gain))
        except Exception as e:
            print(f"Error evaluating question '{question}': {str(e)}")
            info_gains.append((question, 0.0))
    
    # Sort by information gain in descending order
    info_gains.sort(key=lambda x: x[1], reverse=True)
    
    # Return the question with the highest information gain
    if info_gains:
        best_question, best_gain = info_gains[0]
        print(f"\nBest question found with information gain {best_gain:.4f}:")
        print(f"Question: {best_question}")
        return best_question
    else:
        return "Do you have any other symptoms you haven't mentioned?"

def get_initial_probabilities(patient_info: str, num_diseases: int = 10) -> List[Tuple[str, float]]:
    """Get initial disease probabilities from the patient information."""
    # Use probabilistic_inference function from main.py if it's imported
    # Otherwise, we'll implement a simplified version here
    try:
        from main import probabilistic_inference
        return probabilistic_inference(patient_info, num_diseases)
    except ImportError:
        # Fallback implementation if probabilistic_inference isn't available
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": f"""
You are an expert medical diagnosis assistant. Based on the patient information provided below, determine the top {num_diseases} most likely diagnoses, ordered from most to least likely with their probabilities.

Patient Information: {patient_info}

Instructions:
1. Return EXACTLY {num_diseases} diseases with their probabilities
2. Probabilities must sum to exactly 1.0
3. Format each line as: Disease name|0.XXX
4. Use the FULL, proper medical name for each diagnosis
5. Do not include any additional text or explanations
"""}
            ]
        )
        
        diseases = []
        for line in response.choices[0].message.content.strip().split('\n'):
            if '|' in line:
                name, prob = line.split('|', 1)
                try:
                    diseases.append((name.strip(), float(prob.strip())))
                except ValueError:
                    pass
        
        return diseases

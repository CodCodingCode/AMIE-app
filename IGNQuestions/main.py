from openai import OpenAI
import os
import json
from api_key import key
from information_gain import information_gain_network

API_KEY = key
client = OpenAI(api_key=API_KEY)

def load_cases(filename="medical_cases.json"):
    """Load cases from JSON file"""
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading cases: {e}")
        return []

def probabilistic_inference(doctor_vignette, num_diseases=10):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": f"""
You are an expert medical diagnosis assistant with extensive knowledge of internal medicine, symptomatology, and differential diagnosis. 
Based on the information provided below, determine the SPECIFIC top {num_diseases} most likely diagnoses along with their updated probabilities.

Patient Information: {doctor_vignette}

### Medical Knowledge Guidelines:
- Consider the epidemiology and prevalence of different conditions
- Analyze the temporal sequence of symptom development
- Evaluate risk factors and comorbidities
- Assess the specificity and sensitivity of reported symptoms
- Factor in demographic information appropriately
- Recognize common symptom patterns and clinical presentations
- Consider both common and rare diagnoses that fit the symptom profile

### Key Instructions:
- Consider how each new piece of information impacts the differential diagnosis
- Adjust probabilities based on justifiable evidence. Once updated, normalize the set so the total equals 1.00000 exactly
- If a symptom is not relevant to a condition, do not adjust that condition's probability.
- Your output should be explainable—each probability should reflect an evidence-based assessment.
- Always use the FULL, proper medical name for each diagnosis (e.g., "Heart Failure" not "Failure", "Chronic Obstructive Pulmonary Disease" not "COPD")
- You MUST return EXACTLY {num_diseases} diagnoses, even if some have very low probabilities.

### CRITICAL OUTPUT FORMAT:
You MUST return EXACTLY {num_diseases} diagnoses with their probabilities, formatted as follows:

Disease name 1|0.XXX
Disease name 2|0.XXX
Disease name 3|0.XXX
Disease name 4|0.XXX
Disease name 5|0.XXX
(etc. until you have provided exactly {num_diseases} diseases)

Where:
- Each disease-probability pair must be on its own line
- Use the pipe character | between disease name and probability
- The sum of all probabilities MUST equal 1.00000 EXACTLY
- Do not include any narrative text, explanations, or additional information

Before outputting the probabilities, make sure to normalize them so the total equals 1.00000 exactly. Do whatever you need to normalize them. 

This exact format is required for automated parsing. Do not deviate from it in any way.
"""}
        ]
    )
    answer = response.choices[0].message.content
    diseases = []
    for line in answer.split('\n'):
        if '|' in line:
            name, prob = line.split('|', 1)
            diseases.append((name.strip(), float(prob.strip())))
    return diseases

def process_cases():
    # Load cases from JSON file
    try:
        with open("medical_cases.json", "r") as f:
            cases = json.load(f)
    except FileNotFoundError:
        print("Error: medical_cases.json file not found. Please make sure the file exists in the current directory.")
        return
    except json.JSONDecodeError:
        print("Error: medical_cases.json is not a valid JSON file.")
        return
        
    if not cases:
        print("No cases found in medical_cases.json")
        return
        
    results = []
    
    # Create or clear results.json
    with open('results.json', 'w') as f:
        json.dump([], f)
    
    for case_idx, case in enumerate(cases, 1):
        case_result = {
            "case_number": case_idx,
            "doctor_vignette": case['doctor_vignette'],
            "actual_diagnosis": case['actual_diagnosis'],
            "diseases": [],
            "question": ""
        }
        
        print(f"\nProcessing Case {case_idx}...")
        doctor_vignette = case['doctor_vignette']
        diseases_with_probs = probabilistic_inference(doctor_vignette)
        diseases = [disease for disease, _ in diseases_with_probs]
        
        # Store all diseases
        case_result["diseases"] = diseases
        
        # Generate question using information gain network
        question = information_gain_network(doctor_vignette, diseases)
        case_result["question"] = question
        
        print(f"\nAll Diseases (most to least likely):")
        for i, (disease, prob) in enumerate(diseases_with_probs, 1):
            print(f"{i}. {disease} ({prob:.3f})")
        print(f"\nActual Diagnosis: {case['actual_diagnosis']}")
        print(f"Generated Question: {question}")
        
        # Add the new case result
        results.append(case_result)
        
        # Update results.json after each case
        with open('results.json', 'w') as f:
            json.dump(results, f, indent=2)
        print("\nUpdated results.json with current case")
    
    print(f"\nTotal cases processed: {len(cases)}")
    print("\nFinal results have been saved to results.json")

def main():
    # Original code for testing probabilistic_inference
    doctor_vignette = "A 50-year-old male presents with acute chest pain. He is a smoker and has a family history of heart disease. On examination, he has a palpable thrill in the left sternal border and a systolic murmur heard best in the second intercostal space. ECG shows ST-segment elevation in leads V1-V3."
    diseases = probabilistic_inference(doctor_vignette)
    print(diseases)
    
    # Process all cases
    process_cases()

if __name__ == "__main__":
    main()

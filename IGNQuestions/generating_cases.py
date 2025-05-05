from openai import OpenAI
import json
import time
import os
from typing import Dict, List
from concurrent.futures import ThreadPoolExecutor, as_completed
from api_key import key

# Set your OpenAI API key
API_KEY = key

# Track generated diseases
generated_diseases: List[str] = []

def validate_case(case):
    # Ensure the case is a dict with the required fields and non-empty values
    if not isinstance(case, dict):
        return False
    if "doctor_vignette" not in case or "actual_diagnosis" not in case:
        return False
    if not case["doctor_vignette"].strip() or not case["actual_diagnosis"].strip():
        return False
    return True

def parse_case_response(response_content):
    # Try to parse as JSON, fallback to extracting fields manually
    try:
        # First try to find JSON content within the response
        start_idx = response_content.find('{')
        end_idx = response_content.rfind('}')
        if start_idx != -1 and end_idx != -1:
            json_str = response_content[start_idx:end_idx+1]
            case = json.loads(json_str)
            if validate_case(case):
                return case
    except Exception:
        pass
    
    # Fallback: try to extract fields manually
    try:
        lines = response_content.splitlines()
        vignette = ""
        diagnosis = ""
        for line in lines:
            if 'doctor_vignette' in line.lower():
                vignette = line.split(':', 1)[-1].strip(' ",')
            if 'actual_diagnosis' in line.lower():
                diagnosis = line.split(':', 1)[-1].strip(' ",')
        if vignette and diagnosis:
            return {"doctor_vignette": vignette, "actual_diagnosis": diagnosis}
    except Exception:
        pass
    return None

def validate_diagnosis(diagnosis: str, diseases_to_avoid: List[str]) -> bool:
    """Validate that the diagnosis is not in the list of diseases to avoid."""
    diagnosis_lower = diagnosis.lower()
    for disease in diseases_to_avoid:
        if disease.lower() in diagnosis_lower or diagnosis_lower in disease.lower():
            print(f"REJECTED: '{diagnosis}' is too similar to existing diagnosis '{disease}'")
            return False
    return True

def generate_unique_diseases(num_diseases: int = 500) -> List[str]:
    """Generate a list of unique medical diagnoses with ICD-10 codes."""
    prompt = """You are an expert physician. Generate a list of unique medical diagnoses with their ICD-10 codes.
    Each diagnosis must be:
    1. A real medical condition with a valid ICD-10 code
    2. Completely distinct from other diagnoses (no variations or subtypes)
    3. Cover a wide range of medical specialties
    4. Include both common and rare conditions
    
    Format each diagnosis as: "Diagnosis name, ICD-10 code X00.0"
    Separate each diagnosis with a newline.
    
    Example:
    Acute appendicitis, ICD-10 code K35.2
    Pulmonary embolism, ICD-10 code I26.9
    Multiple sclerosis, ICD-10 code G35
    """
    
    diseases = []
    print(f"\nGenerating unique diseases (target: {num_diseases})...")
    
    while len(diseases) < num_diseases:
        try:
            client = OpenAI(api_key=API_KEY)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert physician. Generate unique medical diagnoses with ICD-10 codes."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            content = response.choices[0].message.content
            new_diseases = [line.strip() for line in content.split('\n') if line.strip()]
            
            # Validate and add unique diseases
            for disease in new_diseases:
                if disease not in diseases:
                    diseases.append(disease)
                    print(f"Generated unique disease {len(diseases)}/{num_diseases}: {disease}")
                    if len(diseases) >= num_diseases:
                        break
                        
        except Exception as e:
            print(f"Error generating diseases: {e}")
            time.sleep(1)
    
    print(f"\nSuccessfully generated {len(diseases)} unique diseases!")
    return diseases[:num_diseases]

def generate_case_for_disease(disease: str) -> Dict:
    """Generate a medical case for a specific disease."""
    prompt = f"""You are an expert physician. Generate a realistic medical case for this diagnosis: {disease}

CRITICAL REQUIREMENTS:
1. The vignette must be 3-4 sentences maximum
2. Choose appropriate demographics (age and sex) that are typical for this condition
3. The vignette must be clinically accurate for the diagnosis
4. The vignette must include: demographics, chief complaint, key physical exam findings, and critical lab/imaging results

Output format (must be valid JSON):
{{
    "doctor_vignette": "A concise medical vignette that includes: 1) Demographics (age, sex), 2) Chief complaint, 3) Key physical exam findings, and 4) Critical lab/imaging results",
    "actual_diagnosis": "{disease}"
}}

Generate a case following the exact format above, ensuring the vignette is appropriate for the typical demographic affected by {disease}."""

    content = None
    for attempt in range(3):
        try:
            client = OpenAI(api_key=API_KEY)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert physician. You must return a valid JSON object with exactly two fields: 'doctor_vignette' and 'actual_diagnosis'."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=150
            )
            content = response.choices[0].message.content
            case = parse_case_response(content)
            if validate_case(case):
                return case
        except Exception as e:
            print(f"Error generating case (attempt {attempt+1}): {e}")
            if content:
                print(f"Response content: {content}")
        time.sleep(1)
    return {"doctor_vignette": "Failed to generate vignette.", "actual_diagnosis": disease}

def generate_cases_parallel(num_cases=500, max_workers=5):
    """Generate cases in parallel using ThreadPoolExecutor"""
    # Load existing cases if any
    cases = load_cases()
    start_idx = len(cases)
    
    if start_idx >= num_cases:
        print(f"Already have {start_idx} cases. No new cases needed.")
        return
    
    print(f"Found {start_idx} existing cases. Generating {num_cases - start_idx} new cases...")
    
    # First generate unique diseases
    print("Generating unique diseases...")
    unique_diseases = generate_unique_diseases(num_cases - start_idx)
    print(f"Generated {len(unique_diseases)} unique diseases")
    
    # Generate cases in parallel
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        futures = [executor.submit(generate_case_for_disease, disease) for disease in unique_diseases]
        
        # Process completed tasks
        for i, future in enumerate(as_completed(futures)):
            try:
                case = future.result()
                cases.append(case)
                
                # Save after each case
                save_cases(cases)
                
                # Print progress
                print(f"\nGenerated case {start_idx + i + 1}/{num_cases}:")
                print(f"Diagnosis: {case['actual_diagnosis']}")
                print(f"Vignette: {case['doctor_vignette']}")
                print("-" * 80)
                
            except Exception as e:
                print(f"Error processing case: {e}")
    
    print(f"\nGeneration complete! Total cases: {len(cases)}")
    print("Results have been saved to 'medical_cases.json'")

def save_cases(cases, filename="medical_cases.json"):
    """Save cases to JSON file with pretty printing"""
    with open(filename, 'w') as f:
        json.dump(cases, f, indent=2)

def load_cases(filename="medical_cases.json"):
    """Load existing cases from JSON file"""
    try:
        with open(filename, 'r') as f:
            cases = json.load(f)
            # Initialize the generated_diseases list with diseases from existing cases
            global generated_diseases
            generated_diseases = [case["actual_diagnosis"] for case in cases]
            return cases
    except (FileNotFoundError, json.JSONDecodeError):
        return []

if __name__ == "__main__":
    generate_cases_parallel(num_cases=500, max_workers=5)
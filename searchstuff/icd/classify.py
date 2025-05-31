import pandas as pd
from openai import OpenAI
import os
import textwrap
from concurrent.futures import ThreadPoolExecutor, as_completed

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def classify_diseases(batch):
    diseases_text = "\n".join(batch)
    prompt = textwrap.dedent(f"""\
        You are a medical expert tasked with classifying medical terms into strict categories. You must be EXTREMELY STRICT about what qualifies as an actual disease or disorder.

        STRICT DEFINITIONS:
        - DISEASE/DISORDER: A pathological condition with identifiable etiology, pathophysiology, and clinical course that requires medical diagnosis and treatment. Must be an actual medical condition that affects normal bodily function.
        - SYMPTOMS: Individual manifestations or complaints (e.g., "pain", "fever", "nausea")
        - INJURIES: Acute trauma or damage to body parts (e.g., "fracture", "wound", "burn")
        - PROCEDURES/EVENTS: Medical interventions, exposures, or situational occurrences
        - ANATOMICAL DESCRIPTORS: Normal body parts or anatomical references

        Categories (BE VERY STRICT):
        - Common Diseases/Conditions: Well-established diseases/disorders seen frequently in clinical practice (diabetes, hypertension, pneumonia, depression, etc.)
        - Emergency Diseases/Conditions: Serious diseases/disorders requiring immediate medical intervention (myocardial infarction, stroke, sepsis, etc.)
        - Rare Diseases/Conditions: Legitimate but uncommon diseases/disorders with defined pathophysiology
        - Not a Disease/Condition: Everything else including symptoms, injuries, procedures, exposures, anatomical terms, or vague descriptors

        EXAMPLES OF STRICT CLASSIFICATION:
        ✓ "Type 2 Diabetes Mellitus" → Common Diseases/Conditions (actual metabolic disorder)
        ✓ "Acute Myocardial Infarction" → Emergency Diseases/Conditions (actual cardiac pathology)
        ✓ "Huntington Disease" → Rare Diseases/Conditions (genetic neurodegenerative disorder)
        ✗ "Pain in throat" → Not a Disease/Condition (symptom, not a disorder)
        ✗ "Injury of colon unspecified" → Not a Disease/Condition (injury/trauma, not pathological disorder)
        ✗ "Fracture of femur" → Not a Disease/Condition (acute injury, not disease process)
        ✗ "Exposure to toxic substances" → Not a Disease/Condition (event/exposure, not disorder)
        ✗ "Fever unspecified" → Not a Disease/Condition (symptom, not disorder)
        ✗ "Wound of head" → Not a Disease/Condition (injury, not pathological condition)
        ✗ "Poisoning by medications" → Not a Disease/Condition (acute event, not chronic disorder)

        CRITICAL RULES:
        1. If it's a SYMPTOM (pain, fever, nausea, headache) → "Not a Disease/Condition"
        2. If it's an INJURY/TRAUMA (fracture, wound, burn, laceration) → "Not a Disease/Condition"
        3. If it's an EXPOSURE/EVENT (poisoning, radiation exposure) → "Not a Disease/Condition"
        4. If it's ANATOMICAL (without pathology) → "Not a Disease/Condition"
        5. If it's UNSPECIFIED without clear pathophysiology → "Not a Disease/Condition"
        6. Only classify as disease if it represents a true pathological disorder with defined disease process

        Respond using the following strict format, exactly (DO NOT include line numbers):
        Disease Name: <exact disease name from the list>, Category: <one of the 4 categories above>

        Important:
        - Do NOT modify the disease names.
        - Do NOT skip any diseases.
        - Only respond with {len(batch)} lines in the exact format.
        - Do NOT include extra explanations or commentary.
        - BE EXTREMELY STRICT - when in doubt, classify as "Not a Disease/Condition"

        Classify the following {len(batch)} diseases:
        {diseases_text}
    """)

    response = client.responses.create(
        model="gpt-4o-mini",
        input=prompt,
    )
    return response.output_text

def parse_response(response_text, expected_diseases):
    lines = response_text.strip().split('\n')
    parsed = {}
    
    print(f"  Raw response has {len(lines)} lines")
    print(f"  Expected {len(expected_diseases)} diseases")
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Remove numbers like "1. " from start
        if line and line[0].isdigit() and '. ' in line:
            line = line.split('. ', 1)[1]
        
        # Debug: show what we're trying to parse
        if "Disease Name:" in line and "Category:" in line:
            # Handle the expected format: "Disease Name: ..., Category: ..."
            try:
                name_part, category_part = line.split(", Category:")
                disease = name_part.replace("Disease Name:", "").strip()
                category = category_part.strip()
                parsed[disease] = category
            except:
                print(f"    Parse error on line: {line}")
        elif ", Category:" in line:
            # Handle the actual format: "Disease Name, Category: ..."
            try:
                parts = line.split(", Category:")
                if len(parts) == 2:
                    disease = parts[0].strip()
                    category = parts[1].strip()
                    parsed[disease] = category
            except:
                print(f"    Parse error on line: {line}")
    
    print(f"  Successfully parsed {len(parsed)} diseases")
    return parsed

def process_batch(batch_data):
    batch, batch_num = batch_data
    print(f"Processing batch {batch_num} ({len(batch)} diseases)...")
    
    response_text = classify_diseases(batch)
    
    # Save raw response
    with open("realdatasets/all_responses2.txt", "a", encoding='utf-8') as f:
        f.write(f"\n=== Batch {batch_num} ===\n")
        f.write(response_text.strip() + "\n")
    
    parsed = parse_response(response_text, batch)
    
    results = []
    for disease in batch:
        category = parsed.get(disease, "")
        results.append({
            "Title": disease,
            "Category": category,
            "ParseError": category == ""
        })
    
    # Live update CSV
    output_path = "realdatasets/classified_diseases_live2.csv"
    if os.path.exists(output_path):
        existing_df = pd.read_csv(output_path)
        all_results = existing_df.to_dict('records') + results
    else:
        all_results = results
    
    pd.DataFrame(all_results).to_csv(output_path, index=False)
    
    print(f"Batch {batch_num}: {len(parsed)} classified, {len(batch) - len(parsed)} errors")
    return results

def main():
    # Load data
    df = pd.read_csv('datasets/icd_codes.csv')
    all_diseases = df['Title'].dropna().astype(str).str.strip().tolist()

    # Clear/create output files
    output_path = "realdatasets/classified_diseases_live2.csv"
    response_path = "realdatasets/all_responses2.txt"
    
    if os.path.exists(output_path):
        os.remove(output_path)
    if os.path.exists(response_path):
        os.remove(response_path)

    # Create batches
    batch_size = 50  # Reduced from 50 to avoid token limits
    batches = []
    for i in range(0, len(all_diseases), batch_size):
        batch = all_diseases[i:i+batch_size]
        batch_num = (i // batch_size) + 1
        batches.append((batch, batch_num))

    print(f"Processing {len(all_diseases)} diseases in {len(batches)} batches...")
    
    # Process in parallel
    all_results = []
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(process_batch, batch_data) for batch_data in batches]
        
        for future in as_completed(futures):
            results = future.result()
            all_results.extend(results)
    
    # Stats
    successful = sum(1 for r in all_results if not r['ParseError'])
    failed = len(all_results) - successful
    
    print(f"\nDone! {successful} classified, {failed} failed")
    print(f"Results saved to: {output_path}")
    print(f"Raw responses saved to: {response_path}")

if __name__ == "__main__":
    main()
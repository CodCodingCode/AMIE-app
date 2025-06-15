import pandas as pd
from openai import OpenAI
import os
import json
import time
from typing import List, Dict

def process_diseases_with_openai(df: pd.DataFrame, batch_size: int = 20) -> pd.DataFrame:
    """
    Use OpenAI to intelligently deduplicate diseases by processing in batches
    and using structured output for reliable results.
    """
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    # Get unique diseases to avoid processing obvious duplicates
    unique_diseases = df['common_name'].unique().tolist()
    print(f"Processing {len(unique_diseases)} unique disease names...")
    
    # Process in batches to avoid token limits and improve accuracy
    processed_diseases = {}
    
    for i in range(0, len(unique_diseases), batch_size):
        batch = unique_diseases[i:i + batch_size]
        print(f"Processing batch {i//batch_size + 1}/{(len(unique_diseases)-1)//batch_size + 1}")
        
        # Create a more structured prompt with examples
        prompt = f"""
You are a medical expert tasked with identifying duplicate disease names in a list.

INSTRUCTIONS:
1. Look for diseases that refer to the same condition but have different names
2. Group duplicates together and choose the most commonly used medical term
3. Keep distinct diseases separate even if they're related
4. Return a JSON object mapping each input disease to its canonical name

EXAMPLES:
- "Flu" and "Influenza" → both map to "Influenza" 
- "Pink eye" and "Conjunctivitis" → both map to "Conjunctivitis"
- "Heart attack" and "Myocardial infarction" → both map to "Myocardial infarction"
- "Cold" and "Pneumonia" → keep separate (different conditions)

INPUT DISEASES:
{json.dumps(batch, indent=2)}

Return your response as a JSON object where each key is an input disease name and each value is the canonical name to use. If a disease has no duplicates, map it to itself.

Example format:
{{
    "Disease A": "Disease A",
    "Disease B": "Canonical Disease Name",
    "Disease C": "Canonical Disease Name"
}}
"""

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a medical expert who identifies duplicate disease names and returns structured JSON responses."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # Low temperature for consistency
                response_format={"type": "json_object"}
            )
            
            # Parse the JSON response
            mapping = json.loads(response.choices[0].message.content)
            processed_diseases.update(mapping)
            
        except Exception as e:
            print(f"Error processing batch {i//batch_size + 1}: {e}")
            # Fallback: map each disease to itself
            for disease in batch:
                processed_diseases[disease] = disease
        
        # Small delay to respect rate limits
        time.sleep(0.5)
    
    # Apply the mapping to the dataframe
    df_cleaned = df.copy()
    df_cleaned['common_name'] = df_cleaned['common_name'].map(processed_diseases)
    
    # Remove duplicates that were created by the mapping
    df_cleaned = df_cleaned.drop_duplicates(subset=['common_name'], keep='first')
    
    return df_cleaned, processed_diseases

def analyze_deduplication_results(original_df: pd.DataFrame, cleaned_df: pd.DataFrame, 
                                mapping: Dict[str, str]) -> None:
    """Analyze and report on the deduplication results"""
    
    print(f"\n=== DEDUPLICATION RESULTS ===")
    print(f"Original diseases: {len(original_df)}")
    print(f"After deduplication: {len(cleaned_df)}")
    print(f"Removed: {len(original_df) - len(cleaned_df)} duplicates")
    
    # Find diseases that were actually mapped to something different
    actual_changes = {k: v for k, v in mapping.items() if k != v}
    
    if actual_changes:
        print(f"\n=== DISEASE MAPPINGS APPLIED ===")
        for original, canonical in actual_changes.items():
            print(f"  '{original}' → '{canonical}'")
    
    # Show which diseases appeared multiple times in the original data
    original_counts = original_df['common_name'].value_counts()
    duplicates_in_original = original_counts[original_counts > 1]
    
    if len(duplicates_in_original) > 0:
        print(f"\n=== DISEASES THAT APPEARED MULTIPLE TIMES ===")
        for disease, count in duplicates_in_original.items():
            print(f"  '{disease}': {count} times")

def main():
    # Load the data
    df = pd.read_csv("diseases_with_common_names.csv")
    
    print("Starting OpenAI-based disease deduplication...")
    
    # Process with OpenAI
    df_cleaned, disease_mapping = process_diseases_with_openai(df, batch_size=15)
    
    # Analyze results
    analyze_deduplication_results(df, df_cleaned, disease_mapping)
    
    # Save results
    df_cleaned.to_csv("diseases_openai_deduplicated.csv", index=False)
    
    # Save the mapping for reference
    with open("disease_mapping.json", "w") as f:
        json.dump(disease_mapping, f, indent=2)
    
    print(f"\nResults saved to:")
    print(f"  - diseases_openai_deduplicated.csv")
    print(f"  - disease_mapping.json")
    
    return df_cleaned, disease_mapping

# Alternative approach: Two-step process for better accuracy
def two_step_deduplication(df: pd.DataFrame) -> pd.DataFrame:
    """
    Two-step approach: first identify potential duplicates, then confirm with OpenAI
    """
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    # Step 1: Use pandas to find potential duplicates based on string similarity
    from difflib import SequenceMatcher
    
    unique_diseases = df['common_name'].unique()
    potential_duplicates = []
    
    for i, disease1 in enumerate(unique_diseases):
        for disease2 in unique_diseases[i+1:]:
            similarity = SequenceMatcher(None, disease1.lower(), disease2.lower()).ratio()
            if similarity > 0.6:  # Threshold for potential duplicates
                potential_duplicates.append((disease1, disease2, similarity))
    
    if not potential_duplicates:
        print("No potential duplicates found.")
        return df
    
    print(f"Found {len(potential_duplicates)} potential duplicate pairs")
    
    # Step 2: Ask OpenAI to confirm which are actual duplicates
    confirmed_mappings = {}
    
    for disease1, disease2, similarity in potential_duplicates:
        prompt = f"""
Are these two disease names referring to the same medical condition?

Disease 1: "{disease1}"
Disease 2: "{disease2}"

Respond with a JSON object:
{{
    "are_same_disease": true/false,
    "canonical_name": "preferred medical term if they are the same",
    "explanation": "brief explanation of your decision"
}}
"""
        
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            
            if result.get("are_same_disease", False):
                canonical = result.get("canonical_name", disease1)
                confirmed_mappings[disease1] = canonical
                confirmed_mappings[disease2] = canonical
                print(f"✓ Confirmed: '{disease1}' and '{disease2}' → '{canonical}'")
            
        except Exception as e:
            print(f"Error processing {disease1} vs {disease2}: {e}")
        
        time.sleep(0.5)  # Rate limiting
    
    # Apply confirmed mappings
    df_cleaned = df.copy()
    if confirmed_mappings:
        df_cleaned['common_name'] = df_cleaned['common_name'].map(
            lambda x: confirmed_mappings.get(x, x)
        )
        df_cleaned = df_cleaned.drop_duplicates(subset=['common_name'], keep='first')
    
    return df_cleaned

if __name__ == "__main__":
    # Run the main deduplication
    df_cleaned, mapping = main()
    
    # Optionally run the two-step approach for comparison
    print("\n" + "="*50)
    print("Running two-step approach for comparison...")
    df_two_step = two_step_deduplication(pd.read_csv("diseases_with_common_names.csv"))
    df_two_step.to_csv("diseases_two_step_deduplicated.csv", index=False)
    print(f"Two-step approach result: {len(df_two_step)} diseases")
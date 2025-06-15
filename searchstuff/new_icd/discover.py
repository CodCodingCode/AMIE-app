from openai import OpenAI
import pandas as pd
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
import re

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Thread-safe counter for progress tracking
progress_lock = Lock()
processed_count = 0

def extract_disease_info(disease_name):
    """
    Use OpenAI to extract prevalence, category, and acute/chronic info about the disease
    """
    global processed_count
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "user", 
                "content": f"""Provide information about the following disease/condition. Return the information in this exact format:

DISEASE_NAME: [cleaned disease name without 'due to' clauses]
PREVALENCE_PERCENTAGE: [global prevalence as a percentage number only, e.g., 2.5 for 2.5%]
CATEGORY: [disease category, e.g., "Infectious Disease", "Gastrointestinal Disorder", etc.]
ACUTE_CHRONIC: [Acute/Chronic/Both]

If prevalence data is uncertain, provide your best estimate based on available medical literature.

Disease to analyze: "{disease_name}"
"""
            }],
            temperature=0.1,
            max_tokens=200
        )
        
        response_text = response.choices[0].message.content.strip()
        
        # Parse the structured response
        info = parse_disease_response(response_text, disease_name)
        
        # Update progress counter (thread-safe)
        with progress_lock:
            processed_count += 1
            if processed_count % 5 == 0:
                print(f"Processed {processed_count} diseases...")
        
        return disease_name, info
        
    except Exception as e:
        print(f"Error processing '{disease_name}': {e}")
        with progress_lock:
            processed_count += 1
        # Return default values if error occurs
        return disease_name, {
            'cleaned_name': disease_name,
            'prevalence_percentage': 0.0,
            'category': 'Unknown',
            'acute_chronic': 'Unknown'
        }

def parse_disease_response(response_text, original_disease):
    """
    Parse the structured response from OpenAI
    """
    info = {
        'cleaned_name': original_disease,
        'prevalence_percentage': 0.0,
        'category': 'Unknown',
        'acute_chronic': 'Unknown'
    }
    
    try:
        lines = response_text.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('DISEASE_NAME:'):
                info['cleaned_name'] = line.replace('DISEASE_NAME:', '').strip()
            elif line.startswith('PREVALENCE_PERCENTAGE:'):
                prevalence_str = line.replace('PREVALENCE_PERCENTAGE:', '').strip()
                # Extract number from string
                numbers = re.findall(r'\d+\.?\d*', prevalence_str)
                if numbers:
                    info['prevalence_percentage'] = float(numbers[0])
            elif line.startswith('CATEGORY:'):
                info['category'] = line.replace('CATEGORY:', '').strip()
            elif line.startswith('ACUTE_CHRONIC:'):
                info['acute_chronic'] = line.replace('ACUTE_CHRONIC:', '').strip()
    except Exception as e:
        print(f"Error parsing response for {original_disease}: {e}")
    
    return info

def process_diseases_parallel(diseases, max_workers=8):
    """
    Process diseases in parallel using ThreadPoolExecutor
    """
    results = {}
    
    print(f"Processing {len(diseases)} diseases with {max_workers} parallel workers...")
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_disease = {
            executor.submit(extract_disease_info, disease): disease 
            for disease in diseases
        }
        
        # Collect results as they complete
        for future in as_completed(future_to_disease):
            original_disease, disease_info = future.result()
            results[original_disease] = disease_info
    
    return results

# Read the CSV file
df = pd.read_csv("common_diseases_cleaned.csv")

# Get unique diseases to avoid processing duplicates unnecessarily
unique_diseases = df["disease"].unique()
print(f"Found {len(unique_diseases)} unique diseases to process")

# Process diseases in parallel
start_time = time.time()
disease_info_results = process_diseases_parallel(unique_diseases, max_workers=8)
end_time = time.time()

print(f"\nCompleted processing in {end_time - start_time:.2f} seconds")

# Create new dataframe with disease information
enhanced_data = []
for original_disease in unique_diseases:
    info = disease_info_results[original_disease]
    enhanced_data.append({
        'original_disease': original_disease,
        'cleaned_disease': info['cleaned_name'],
        'prevalence_percentage': info['prevalence_percentage'],
        'category': info['category'],
        'acute_chronic': info['acute_chronic'],
        'verified_classification': df[df['disease'] == original_disease]['verified_classification'].iloc[0]
    })

# Create enhanced dataframe
df_enhanced = pd.DataFrame(enhanced_data)

# Filter to keep only diseases with prevalence above 1%
df_filtered = df_enhanced[df_enhanced['prevalence_percentage'] > 1.0]

print(f"\nResults:")
print(f"Original unique diseases: {len(df_enhanced)}")
print(f"Diseases with >1% prevalence: {len(df_filtered)}")
print(f"Filtered out: {len(df_enhanced) - len(df_filtered)} diseases")

# Save both the full enhanced data and the filtered data
df_enhanced.to_csv("diseases_enhanced_full.csv", index=False)
df_filtered.to_csv("diseases_enhanced_filtered.csv", index=False)

# Show some examples
print(f"\nExamples of enhanced disease data:")
for _, row in df_filtered.head(10).iterrows():
    print(f"Disease: {row['cleaned_disease']}")
    print(f"  Prevalence: {row['prevalence_percentage']}%")
    print(f"  Category: {row['category']}")
    print(f"  Type: {row['acute_chronic']}")
    print()

print(f"Enhanced data saved to 'diseases_enhanced_full.csv'")
print(f"Filtered data (>1% prevalence) saved to 'diseases_enhanced_filtered.csv'")
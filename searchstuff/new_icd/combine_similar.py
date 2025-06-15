from openai import OpenAI
import pandas as pd
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
import numpy as np

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Thread-safe counter for progress tracking
progress_lock = Lock()
processed_count = 0

def extract_core_disease(disease_name):
    """
    Use OpenAI to extract the core disease name, removing 'due to' clauses and similar
    """
    global processed_count
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "user", 
                "content": f"""Extract only the core disease name from this medical term, removing any 'due to', 'caused by', 'secondary to', or similar phrases. Just return the main disease/condition name.

Examples:
- "Intestinal infection due to other Vibrio" → "Intestinal infection"
- "Gastroenteritis due to Campylobacter" → "Gastroenteritis" 
- "Enteritis due to Norovirus" → "Enteritis"
- "Giardiasis" → "Giardiasis" (already clean)

Disease to clean: "{disease_name}"

Return only the cleaned disease name, nothing else:"""
            }],
            temperature=0.1,  # Low temperature for consistency
            max_tokens=50
        )
        
        cleaned_name = response.choices[0].message.content.strip()
        
        # Update progress counter (thread-safe)
        with progress_lock:
            processed_count += 1
            if processed_count % 10 == 0:  # Print progress every 10 items
                print(f"Processed {processed_count} diseases...")
        
        return disease_name, cleaned_name
        
    except Exception as e:
        print(f"Error processing '{disease_name}': {e}")
        with progress_lock:
            processed_count += 1
        return disease_name, disease_name  # Return original if there's an error

def process_diseases_parallel(diseases, max_workers=10):
    """
    Process diseases in parallel using ThreadPoolExecutor
    """
    results = {}
    
    print(f"Processing {len(diseases)} diseases with {max_workers} parallel workers...")
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_disease = {
            executor.submit(extract_core_disease, disease): disease 
            for disease in diseases
        }
        
        # Collect results as they complete
        for future in as_completed(future_to_disease):
            original_disease, cleaned_disease = future.result()
            results[original_disease] = cleaned_disease
    
    return results

# Read the CSV file
df = pd.read_csv("common_diseases_standardized.csv")

# Get unique diseases to avoid processing duplicates unnecessarily
unique_diseases = df["disease"].unique()
print(f"Found {len(unique_diseases)} unique diseases to process")

# Process diseases in parallel
start_time = time.time()
cleaned_results = process_diseases_parallel(unique_diseases, max_workers=10)
end_time = time.time()

print(f"\nCompleted processing in {end_time - start_time:.2f} seconds")

# Map the results back to the dataframe
df["cleaned_disease"] = df["disease"].map(cleaned_results)

# Remove duplicates based on the cleaned disease name
print("Removing duplicates...")
df_cleaned = df.drop_duplicates(subset=['cleaned_disease'], keep='first')

# Replace the original disease column with the cleaned version
df_cleaned["disease"] = df_cleaned["cleaned_disease"]
df_cleaned = df_cleaned.drop("cleaned_disease", axis=1)

# Save the cleaned data
df_cleaned.to_csv("common_diseases_cleaned.csv", index=False)

print(f"\nResults:")
print(f"Original dataset: {len(df)} rows")
print(f"Cleaned dataset: {len(df_cleaned)} rows")
print(f"Removed: {len(df) - len(df_cleaned)} duplicate diseases")

# Show examples of the cleaning
print(f"\nExamples of cleaned disease names:")
sample_diseases = list(unique_diseases)[:10]
for original in sample_diseases:
    cleaned = cleaned_results[original]
    if original != cleaned:
        print(f"'{original}' → '{cleaned}'")
    else:
        print(f"'{original}' (no change needed)")

print(f"\nCleaned data saved to 'common_diseases_cleaned.csv'")
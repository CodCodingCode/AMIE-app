from openai import OpenAI
import pandas as pd
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Thread-safe counter for progress tracking
progress_lock = Lock()
processed_count = 0

def assess_disease_specificity(disease_name):
    """
    Use OpenAI to determine if a disease is specific enough or just a broad category
    """
    global processed_count
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "user", 
                "content": f"""Determine if this disease/condition name is SPECIFIC or GENERIC.

SPECIFIC diseases are:
- Named after specific pathogens (e.g., "Giardiasis", "Streptococcal pharyngitis", "Dengue")
- Have specific medical names (e.g., "Conjunctivitis", "Trichomoniasis", "Influenza")
- Reference particular conditions (e.g., "Hepatitis B", "Herpes simplex infection")

GENERIC diseases are:
- Broad categories (e.g., "Intestinal infection", "Pulmonary infection", "Infections")
- General terms (e.g., "Gastroenteritis", "Respiratory illness", "Skin condition")
- Umbrella terms that could include many specific diseases

Disease to evaluate: "{disease_name}"

Respond with ONLY one word: SPECIFIC or GENERIC"""
            }],
            temperature=0.1,
            max_tokens=10
        )
        
        classification = response.choices[0].message.content.strip().upper()
        
        # Update progress counter (thread-safe)
        with progress_lock:
            processed_count += 1
            if processed_count % 5 == 0:
                print(f"Processed {processed_count} diseases...")
        
        return disease_name, classification
        
    except Exception as e:
        print(f"Error processing '{disease_name}': {e}")
        with progress_lock:
            processed_count += 1
        return disease_name, "GENERIC"  # Default to GENERIC if error

def process_diseases_parallel(diseases, max_workers=10):
    """
    Process diseases in parallel using ThreadPoolExecutor
    """
    results = {}
    
    print(f"Evaluating specificity of {len(diseases)} diseases with {max_workers} parallel workers...")
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_disease = {
            executor.submit(assess_disease_specificity, disease): disease 
            for disease in diseases
        }
        
        # Collect results as they complete
        for future in as_completed(future_to_disease):
            disease_name, classification = future.result()
            results[disease_name] = classification
    
    return results

# Read the enhanced CSV file
df = pd.read_csv("diseases_enhanced_filtered.csv")

print(f"Loaded {len(df)} diseases from enhanced filtered data")

# Get unique cleaned diseases to evaluate
unique_diseases = df["cleaned_disease"].unique()
print(f"Found {len(unique_diseases)} unique diseases to evaluate for specificity")

# Process diseases in parallel to determine specificity
start_time = time.time()
specificity_results = process_diseases_parallel(unique_diseases, max_workers=10)
end_time = time.time()

print(f"\nCompleted specificity evaluation in {end_time - start_time:.2f} seconds")

# Add specificity classification to dataframe
df["specificity"] = df["cleaned_disease"].map(specificity_results)

# Filter to keep only specific diseases
df_specific = df[df["specificity"] == "SPECIFIC"]

# Remove the specificity column from final output (optional)
df_specific = df_specific.drop("specificity", axis=1)

print(f"\nFiltering Results:")
print(f"Total diseases: {len(df)}")
print(f"Specific diseases: {len(df_specific)}")
print(f"Generic diseases removed: {len(df) - len(df_specific)}")

# Show what was kept vs removed
print(f"\nSpecific diseases kept:")
for disease in df_specific["cleaned_disease"].unique()[:10]:
    print(f"  ✓ {disease}")

print(f"\nGeneric diseases removed:")
generic_diseases = df[df["specificity"] == "GENERIC"]["cleaned_disease"].unique()
for disease in generic_diseases[:10]:
    print(f"  ✗ {disease}")

if len(generic_diseases) > 10:
    print(f"  ... and {len(generic_diseases) - 10} more")

# Save the filtered specific diseases
df_specific.to_csv("diseases_specific_only.csv", index=False)

print(f"\nSpecific diseases saved to 'diseases_specific_only.csv'")
print(f"Final dataset contains {len(df_specific)} specific diseases")

# Show prevalence distribution of specific diseases
print(f"\nPrevalence distribution of specific diseases:")
prevalence_ranges = [
    (1, 5, "1-5%"),
    (5, 10, "5-10%"), 
    (10, 20, "10-20%"),
    (20, 50, "20-50%"),
    (50, 100, "50%+")
]

for min_prev, max_prev, label in prevalence_ranges:
    count = len(df_specific[
        (df_specific["prevalence_percentage"] >= min_prev) & 
        (df_specific["prevalence_percentage"] < max_prev)
    ])
    if min_prev == 50:  # Last range is 50%+
        count = len(df_specific[df_specific["prevalence_percentage"] >= min_prev])
    print(f"  {label}: {count} diseases")
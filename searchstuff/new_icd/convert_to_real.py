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

def convert_to_common_name(disease_name):
    """
    Convert medical disease name to a more understandable common name using OpenAI
    """
    global processed_count
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "user", 
                "content": f"""Convert this medical disease name to a simple, understandable common name.

IMPORTANT INSTRUCTIONS:
- Return ONLY the common name, nothing else
- No quotes, no explanations, no extra text
- Just the plain disease name that regular people would understand
- If the name is already simple, you may keep it the same

Medical name: {disease_name}

EXAMPLES:
Enterotoxigenic Escherichia coli infection → E. coli food poisoning
Streptococcal pharyngitis → Strep throat
Herpes simplex infection → Herpes
Chlamydial infection → Chlamydia
Giardiasis → Giardia infection
Trichomoniasis → Trichomoniasis
Dengue → Dengue fever

Common name:"""
            }],
            temperature=0.0,  # Zero temperature for maximum consistency
            max_tokens=20,    # Short response to avoid extra text
            stop=["\n", ".", "!"]  # Stop at punctuation to avoid explanations
        )
        
        common_name = response.choices[0].message.content.strip()
        
        # Update progress counter (thread-safe)
        with progress_lock:
            processed_count += 1
            if processed_count % 10 == 0:
                print(f"Processed {processed_count} diseases...")
        
        return disease_name, common_name
        
    except Exception as e:
        print(f"Error processing '{disease_name}': {e}")
        with progress_lock:
            processed_count += 1
        return disease_name, disease_name  # Return original if error

def process_diseases_parallel(diseases, max_workers=10):
    """
    Process diseases in parallel using ThreadPoolExecutor
    """
    results = {}
    
    print(f"Converting {len(diseases)} disease names with {max_workers} parallel workers...")
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_disease = {
            executor.submit(convert_to_common_name, disease): disease 
            for disease in diseases
        }
        
        # Collect results as they complete
        for future in as_completed(future_to_disease):
            original_disease, common_name = future.result()
            results[original_disease] = common_name
    
    return results

def main():
    """
    Main function to convert medical names to common names
    """
    print("=" * 60)
    print("🔄 MEDICAL NAME TO COMMON NAME CONVERTER")
    print("=" * 60)
    
    # Read the CSV file
    df = pd.read_csv("diseases_specific_only.csv")  # Update filename as needed
    
    print(f"📂 Loaded {len(df)} diseases from CSV")
    
    # Get unique disease names to avoid processing duplicates
    unique_diseases = df["cleaned_disease"].unique()
    print(f"🔍 Found {len(unique_diseases)} unique diseases to convert")
    print("-" * 60)
    
    # Process diseases in parallel
    print("🚀 Starting parallel conversion process...")
    start_time = time.time()
    conversion_results = process_diseases_parallel(unique_diseases, max_workers=10)
    end_time = time.time()
    
    print(f"✅ Completed conversion in {end_time - start_time:.2f} seconds")
    print("-" * 60)
    
    # Add the common names to the dataframe
    df["common_name"] = df["cleaned_disease"].map(conversion_results)
    
    # Remove duplicates based on common name
    print("🧹 Removing duplicates based on common names...")
    df_before_dedup = df.copy()
    df = df.drop_duplicates(subset=['common_name'], keep='first')
    
    duplicates_removed = len(df_before_dedup) - len(df)
    print(f"🗑️  Removed {duplicates_removed} duplicate diseases")
    print("-" * 60)
    
    # Show examples of conversions
    print("📝 CONVERSION EXAMPLES:")
    sample_conversions = list(conversion_results.items())[:8]
    for i, (original, common) in enumerate(sample_conversions, 1):
        if original != common:
            print(f"   {i:2}. '{original}'")
            print(f"       ➜ '{common}'")
        else:
            print(f"   {i:2}. '{original}' (unchanged)")
    print("-" * 60)
    
    # Save the updated dataframe
    df.to_csv("diseases_with_common_names.csv", index=False)
    
    print("📊 SUMMARY STATISTICS:")
    print(f"   • Original diseases:        {len(df_before_dedup):,}")
    print(f"   • After deduplication:      {len(df):,}")
    print(f"   • Duplicates removed:       {duplicates_removed:,}")
    
    # Count how many names were actually changed
    changes_made = sum(1 for orig, common in conversion_results.items() if orig != common)
    print(f"   • Names converted:          {changes_made:,}")
    print(f"   • Names kept same:          {len(conversion_results) - changes_made:,}")
    
    # Show examples of duplicates that were removed (if any)
    if duplicates_removed > 0:
        print("-" * 60)
        print("🔄 DUPLICATE EXAMPLES REMOVED:")
        # Find duplicates by checking which common names appear multiple times in original data
        common_name_counts = df_before_dedup['common_name'].value_counts()
        duplicated_names = common_name_counts[common_name_counts > 1].head(5)
        
        for i, (common_name, count) in enumerate(duplicated_names.items(), 1):
            original_diseases = df_before_dedup[df_before_dedup['common_name'] == common_name]['cleaned_disease'].tolist()
            print(f"   {i}. Common name: '{common_name}' ({count} variants)")
            for j, variant in enumerate(original_diseases[:3], 1):
                status = "✅ kept" if j == 1 else "❌ removed"
                print(f"      {j}. {variant} ({status})")
            if len(original_diseases) > 3:
                print(f"      ... and {len(original_diseases) - 3} more variants")
    
    print("-" * 60)
    print("💾 RESULTS SAVED:")
    print(f"   ✅ File: 'diseases_with_common_names.csv'")
    print(f"   📋 Columns added: 'common_name'")
    print(f"   🎯 Ready for patient-friendly use!")
    print("=" * 60)

if __name__ == "__main__":
    # Make sure you have your OpenAI API key set:
    # export OPENAI_API_KEY="your_openai_key"
    
    main()
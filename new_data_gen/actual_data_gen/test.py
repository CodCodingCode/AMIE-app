import json
import os
from openai import OpenAI
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Initialize OpenAI client
client = OpenAI(
    api_key="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"
)
model = "gpt-4.1-nano"

def load_diseases_from_json(filename):
    """Load diseases from the combined.json file"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Handle different JSON structures
        if isinstance(data, list):
            diseases = data
        elif isinstance(data, dict) and "diseases" in data:
            diseases = data["diseases"]
        elif isinstance(data, dict):
            # If it's a dict but no "diseases" key, assume the whole thing is diseases
            diseases = list(data.values()) if all(isinstance(v, dict) for v in data.values()) else [data]
        else:
            print(f"❌ Unexpected JSON structure in {filename}")
            return []
        
        print(f"✅ Loaded {len(diseases)} diseases from {filename}")
        return diseases
        
    except Exception as e:
        print(f"❌ Error loading {filename}: {e}")
        return []

def classify_disease_for_primary_care(disease_data, api_key, model_name):
    """Use ChatGPT to classify if a disease is appropriate for primary care and not a mental illness"""
    
    # Create a new client for thread safety
    thread_client = OpenAI(api_key=api_key)
    
    disease_name = disease_data.get("disease_name", "Unknown Disease")
    symptoms = disease_data.get("symptoms", [])
    causes = disease_data.get("causes", [])
    treatment_options = disease_data.get("treatment_options", [])
    
    # Create prompt for classification
    classification_prompt = f"""
You are a medical expert specializing in primary care medicine. Analyze this disease and determine if it meets BOTH criteria:

DISEASE: {disease_name}

SYMPTOMS: {', '.join(symptoms[:10])}  # First 10 symptoms
CAUSES: {', '.join(causes[:5])}  # First 5 causes  
TREATMENTS: {', '.join(treatment_options[:5])}  # First 5 treatments

CRITERIA TO EVALUATE:
1. Is this disease commonly seen and managed in PRIMARY CARE PRACTICES (family medicine, internal medicine, general practice)?
2. Is this disease NOT a mental illness or psychiatric condition?

EXCLUDE if the disease is:
- Primarily managed by specialists (cardiothoracic surgery, neurosurgery, oncology subspecialties)
- Mental health conditions (depression, anxiety, schizophrenia, bipolar disorder, etc.)
- Rare genetic disorders requiring specialist care
- Advanced cancer requiring oncology
- Complex surgical conditions
- Conditions requiring specialized procedures

INCLUDE if the disease is:
- Common infections, injuries, or conditions seen in primary care
- Chronic conditions managed in primary care (diabetes, hypertension, etc.)
- Acute conditions that primary care doctors diagnose and treat
- Preventive care conditions
- Common dermatology, respiratory, GI conditions handled in primary care

Respond in this exact format:
THINKING: [Your medical reasoning about whether this fits primary care and is not mental illness]
ANSWER: PRIMARY_CARE_SUITABLE or NOT_PRIMARY_CARE_SUITABLE
"""

    try:
        response = thread_client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are a primary care physician with 20+ years of experience. You know exactly which conditions are commonly seen and managed in primary care vs. those requiring specialists."},
                {"role": "user", "content": classification_prompt}
            ],
            temperature=0.3  # Lower temperature for consistent medical decisions
        )
        
        raw_response = response.choices[0].message.content.strip()
        
        # Extract the answer
        if "PRIMARY_CARE_SUITABLE" in raw_response:
            classification = "PRIMARY_CARE_SUITABLE"
        elif "NOT_PRIMARY_CARE_SUITABLE" in raw_response:
            classification = "NOT_PRIMARY_CARE_SUITABLE"
        else:
            classification = "UNCLEAR"
        
        # Extract thinking if available
        thinking = ""
        if "THINKING:" in raw_response:
            thinking = raw_response.split("THINKING:")[1].split("ANSWER:")[0].strip()
        
        return {
            "disease_name": disease_name,
            "classification": classification,
            "reasoning": thinking,
            "raw_response": raw_response,
            "disease_data": disease_data
        }
        
    except Exception as e:
        print(f"❌ Error classifying {disease_name}: {e}")
        return {
            "disease_name": disease_name,
            "classification": "ERROR",
            "reasoning": f"API error: {str(e)}",
            "raw_response": "",
            "disease_data": disease_data
        }


def classify_disease_wrapper(args):
    """Wrapper function for parallel processing"""
    disease_data, api_key, model_name, index, total = args
    disease_name = disease_data.get("disease_name", f"Disease_{index}")
    
    print(f"🔄 [{index+1}/{total}] Analyzing: {disease_name}")
    
    result = classify_disease_for_primary_care(disease_data, api_key, model_name)
    
    if result["classification"] == "PRIMARY_CARE_SUITABLE":
        print(f"✅ [{index+1}/{total}] KEPT: {disease_name}")
    elif result["classification"] == "NOT_PRIMARY_CARE_SUITABLE":
        print(f"🗑️ [{index+1}/{total}] REMOVED: {disease_name}")
    else:
        print(f"⚠️ [{index+1}/{total}] ERROR/UNCLEAR: {disease_name}")
    
    return result

def filter_primary_care_diseases(input_filename="combined.json", output_filename="primary_care_diseases.json", create_filtered_dataset=True, max_workers=8):
    """Main function to filter diseases for primary care suitability with parallel processing"""
    
    print("🏥 PRIMARY CARE DISEASE FILTER - PARALLEL PROCESSING")
    print("=" * 60)
    print("🎯 Finding diseases that are:")
    print("   ✅ Commonly seen in primary care practices")
    print("   ✅ NOT mental illnesses")
    print("🗑️ Mental illnesses and specialist conditions will be REMOVED from dataset")
    print(f"⚡ Using {max_workers} parallel workers for faster processing")
    print("=" * 60)
    
    # Load diseases
    diseases = load_diseases_from_json(input_filename)
    if not diseases:
        print("❌ No diseases loaded. Exiting.")
        return
    
    # Results storage
    primary_care_diseases = []
    excluded_diseases = []
    classification_results = []
    results_lock = threading.Lock()
    
    print(f"\n🔍 Analyzing {len(diseases)} diseases with {max_workers} workers...")
    
    # Prepare arguments for parallel processing
    args_list = [
        (disease_data, client.api_key, model, i, len(diseases))
        for i, disease_data in enumerate(diseases)
    ]
    
    # Process diseases in parallel
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_args = {
            executor.submit(classify_disease_wrapper, args): args
            for args in args_list
        }
        
        completed_count = 0
        
        # Process results as they complete
        for future in as_completed(future_to_args):
            try:
                result = future.result()
                
                with results_lock:
                    completed_count += 1
                    
                    # Store classification result
                    classification_entry = {
                        "disease_name": result["disease_name"],
                        "classification": result["classification"],
                        "reasoning": result["reasoning"],
                        "raw_response": result["raw_response"]
                    }
                    classification_results.append(classification_entry)
                    
                    # Categorize based on result - ONLY keep primary care suitable diseases
                    if result["classification"] == "PRIMARY_CARE_SUITABLE":
                        primary_care_diseases.append(result["disease_data"])
                    else:
                        # Remove all non-primary care diseases (including errors and unclear)
                        excluded_diseases.append({
                            "disease_data": result["disease_data"],
                            "exclusion_reason": result["reasoning"] if result["reasoning"] else "Classification failed or unclear"
                        })
                    
                    # Progress update every 10 completions
                    if completed_count % 10 == 0 or completed_count == len(diseases):
                        progress = (completed_count / len(diseases)) * 100
                        kept_count = len(primary_care_diseases)
                        removed_count = len(excluded_diseases)
                        print(f"📊 Progress: {completed_count}/{len(diseases)} ({progress:.1f}%) - Kept: {kept_count}, Removed: {removed_count}")
                        
            except Exception as e:
                print(f"❌ Error processing result: {e}")
                with results_lock:
                    completed_count += 1
    
    print(f"\n✅ Parallel processing completed!")
    print(f"📊 Final counts: Kept {len(primary_care_diseases)}, Removed {len(excluded_diseases)}")
    
    # Create comprehensive output
    output_data = {
        "metadata": {
            "source_file": input_filename,
            "total_diseases_analyzed": len(diseases),
            "primary_care_suitable": len(primary_care_diseases),
            "excluded_diseases": len(excluded_diseases),
            "analysis_date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "processing_method": f"Parallel processing with {max_workers} workers",
            "criteria": {
                "included": "Diseases commonly seen and managed in primary care practices",
                "excluded": "Mental illnesses, specialist-only conditions, rare genetic disorders, complex surgical conditions"
            },
            "dataset_action": "Mental illnesses and specialist conditions REMOVED from dataset"
        },
        "primary_care_diseases": primary_care_diseases,
        "excluded_diseases": excluded_diseases,
        "detailed_classifications": classification_results
    }
    
    # Save full analysis results
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    # CREATE CLEANED DATASET - ONLY primary care diseases
    if create_filtered_dataset:
        filtered_dataset_filename = "combined_primary_care_only.json"
        
        # Create the cleaned dataset with only primary care diseases
        cleaned_dataset = {
            "metadata": {
                "description": "Diseases dataset filtered for primary care practices only",
                "original_file": input_filename,
                "original_disease_count": len(diseases),
                "filtered_disease_count": len(primary_care_diseases),
                "removed_count": len(excluded_diseases),
                "filter_date": time.strftime("%Y-%m-%d %H:%M:%S"),
                "processing_method": f"Parallel processing with {max_workers} workers",
                "criteria": "Primary care suitable, non-mental illness diseases only"
            },
            "diseases": primary_care_diseases
        }
        
        with open(filtered_dataset_filename, 'w', encoding='utf-8') as f:
            json.dump(cleaned_dataset, f, indent=2, ensure_ascii=False)
        
        print(f"🗑️ CREATED CLEANED DATASET: {filtered_dataset_filename}")
        print(f"   📊 Original dataset: {len(diseases)} diseases")
        print(f"   🧹 Cleaned dataset: {len(primary_care_diseases)} diseases")
        print(f"   🗑️ Removed: {len(excluded_diseases)} diseases")
    
    # Save summary file
    summary_filename = "primary_care_summary.json"
    summary_data = {
        "summary": {
            "total_analyzed": len(diseases),
            "primary_care_suitable": len(primary_care_diseases),
            "removed_count": len(excluded_diseases),
            "removal_rate": f"{(len(excluded_diseases)/len(diseases)*100):.1f}%",
            "retention_rate": f"{(len(primary_care_diseases)/len(diseases)*100):.1f}%",
            "analysis_date": time.strftime("%Y-%m-%d %H:%M:%S")
        },
        "kept_disease_names": [d.get("disease_name", "Unknown") for d in primary_care_diseases],
        "removed_disease_names": [d["disease_data"].get("disease_name", "Unknown") for d in excluded_diseases]
    }
    
    with open(summary_filename, 'w', encoding='utf-8') as f:
        json.dump(summary_data, f, indent=2, ensure_ascii=False)
    
    # Print final summary
    print(f"\n" + "=" * 60)
    print(f"📊 FINAL RESULTS - PARALLEL DATASET CLEANING COMPLETE")
    print(f"=" * 60)
    print(f"📁 Original dataset: {len(diseases)} diseases")
    print(f"✅ Kept for primary care: {len(primary_care_diseases)} diseases")
    print(f"🗑️ Removed (mental illness/specialist): {len(excluded_diseases)} diseases")
    print(f"📈 Retention rate: {(len(primary_care_diseases)/len(diseases)*100):.1f}%")
    print(f"🗑️ Removal rate: {(len(excluded_diseases)/len(diseases)*100):.1f}%")
    print(f"⚡ Processing method: {max_workers} parallel workers")
    
    print(f"\n💾 Files created:")
    print(f"   📋 Analysis results: {output_filename}")
    print(f"   🧹 Cleaned dataset: combined_primary_care_only.json")
    print(f"   📄 Summary: {summary_filename}")
    
    print(f"\n🏥 DISEASES KEPT IN DATASET:")
    for disease in primary_care_diseases:
        print(f"   ✅ {disease.get('disease_name', 'Unknown')}")
    
    print(f"\n🗑️ DISEASES REMOVED FROM DATASET (Top 10):")
    for excluded in excluded_diseases[:10]:
        disease_name = excluded["disease_data"].get("disease_name", "Unknown")
        reason = excluded["exclusion_reason"][:60] + "..." if len(excluded["exclusion_reason"]) > 60 else excluded["exclusion_reason"]
        print(f"   ❌ {disease_name}: {reason}")
    
    if len(excluded_diseases) > 10:
        print(f"   ... and {len(excluded_diseases) - 10} more removed (see analysis file)")
    
    print(f"\n🎯 RECOMMENDATION: Use 'combined_primary_care_only.json' for your primary care training dataset")
    print(f"⚡ Total processing time saved with {max_workers} workers!")
    
    return primary_care_diseases

if __name__ == "__main__":
    if not os.path.exists("combined.json"):
        print("❌ combined.json file not found!")
        print("📁 Please ensure combined.json is in the same directory as this script.")
        exit(1)
    
    print("🚀 Starting Parallel Primary Care Disease Classification and Dataset Cleaning...")
    
    # Configuration
    MAX_WORKERS = 12  # Adjust based on your API rate limits and system
    
    # Run the analysis with parallel processing
    primary_care_diseases = filter_primary_care_diseases(
        input_filename="combined.json",
        output_filename="primary_care_diseases.json",
        create_filtered_dataset=True,
        max_workers=MAX_WORKERS
    )
    
    print(f"\n✅ Parallel analysis and dataset cleaning complete!")
    print(f"🎯 Kept {len(primary_care_diseases)} diseases suitable for primary care practice")
    print(f"🗑️ Mental illnesses and specialist-only conditions have been REMOVED")
    print(f"🧹 Use 'combined_primary_care_only.json' as your cleaned dataset")
    print(f"📋 This dataset contains ONLY diseases commonly managed in primary care settings")
    print(f"⚡ Processing completed using {MAX_WORKERS} parallel workers!")
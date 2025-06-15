import pandas as pd
from openai import OpenAI
import os
import time
import json
from tqdm import tqdm
import concurrent.futures
import threading
from queue import Queue
import signal
import sys

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY").strip())

# Global variables for live updates
update_queue = Queue()
stop_flag = threading.Event()

def classify_diseases_batch(batch_data):
    """
    Classify a batch of disease descriptions into categories.
    batch_data is a tuple: (batch_index, descriptions_batch)
    Returns (batch_index, list_of_classifications)
    """
    batch_index, descriptions_batch = batch_data
    
    # Create numbered list of diseases for the prompt
    disease_list = "\n".join([f"{i+1}. {desc}" for i, desc in enumerate(descriptions_batch)])
    
    prompt = f"""
    Classify each of the following medical entries into exactly one of these five categories:

    1. common disease - frequent, everyday conditions like cold, flu, headache, minor infections, common bacterial/viral infections
    2. emergency disease - life-threatening conditions requiring immediate medical attention
    3. rare disease - uncommon conditions affecting small populations
    4. mental disease - psychiatric or psychological disorders
    5. not a valid entry - non-specific entries, administrative codes, or vague classifications

    IMPORTANT: Use "not a valid entry" for entries that are:
    - Unspecified conditions (e.g., "Disease X unspecified", "Condition Y not otherwise specified")
    - "Other specified" or "other forms" entries (e.g., "Other specified bacterial infections")
    - Administrative/procedural codes (e.g., "Encounter for", "Screening for", "Follow-up", "Examination")
    - Medical procedures or aftercare (e.g., "Counseling", "Supervision of", "Aftercare")
    - Historical tracking (e.g., "Personal history of", "Family history of")
    - Exposure/contact tracking (e.g., "Contact with", "Exposure to", "Carrier of")
    - Diagnostic uncertainty (e.g., "Suspected", "Ruled out", "Provisional diagnosis")
    - Symptom collections without specific disease (e.g., "Symptoms", "Signs", "Abnormal findings")
    - Sequelae or complications without the primary disease
    - Very vague or incomplete descriptions
    - Pure administrative or legal codes

    Medical entries to classify:
    {disease_list}

    IMPORTANT: For each entry, respond in this EXACT format:
    Entry Name: <classification>

    Where <classification> is exactly one of: common disease, emergency disease, rare disease, mental disease, not a valid entry

    Example response:
    Cholera: emergency disease
    Common cold: common disease
    Huntington's disease: rare disease
    Depression: mental disease
    Typhoid fever unspecified: not a valid entry
    Other specified bacterial infections: not a valid entry
    Follow-up examination: not a valid entry

    Respond with exactly {len(descriptions_batch)} lines, one for each entry in the same order.
    """
    
    max_retries = 5
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                max_tokens=3000
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Parse the response
            classifications = parse_disease_classification_response(response_text, descriptions_batch)
            
            if len(classifications) == len(descriptions_batch):
                return (batch_index, classifications)
            else:
                raise ValueError(f"Response mismatch: expected {len(descriptions_batch)} classifications, got {len(classifications)}")
                
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"Error with batch {batch_index}, attempt {attempt + 1}: {e}")
                time.sleep(2 ** attempt)
                continue
    
    # If all retries failed, raise an exception
    raise Exception(f"Batch {batch_index} failed after {max_retries} attempts. Unable to classify this batch.")

def parse_disease_classification_response(response_text, original_descriptions):
    """
    Parse the "Disease Name: classification" format response from OpenAI.
    Returns a list of classifications in the same order as original_descriptions.
    """
    valid_categories = ["common disease", "emergency disease", "rare disease", "mental disease", "not a valid entry"]
    
    # Split response into lines and clean them
    lines = [line.strip() for line in response_text.split('\n') if line.strip()]
    
    print(f"DEBUG: Found {len(lines)} response lines for {len(original_descriptions)} diseases")
    
    # Parse each line
    parsed_classifications = []
    found_diseases = []
    
    for line_num, line in enumerate(lines):
        if ':' not in line:
            print(f"WARNING: Line {line_num + 1} missing colon: '{line}'")
            continue
            
        # Split on the last colon to handle disease names with colons
        parts = line.rsplit(':', 1)
        if len(parts) != 2:
            print(f"WARNING: Line {line_num + 1} invalid format: '{line}'")
            continue
            
        disease_name = parts[0].strip()
        classification = parts[1].strip().lower()
        
        # Remove any numbering from disease name (e.g., "1. Cholera" -> "Cholera")
        if disease_name and disease_name[0].isdigit():
            # Remove leading number and dot/space
            disease_name = disease_name.split('.', 1)[-1].strip()
        
        # Validate classification
        if classification not in valid_categories:
            print(f"WARNING: Invalid classification '{classification}' for disease '{disease_name}'")
            continue
        
        found_diseases.append(disease_name.lower())
        parsed_classifications.append(classification)
    
    # Now match the parsed results back to original descriptions
    final_classifications = []
    
    for original_desc in original_descriptions:
        original_lower = original_desc.lower()
        best_match_idx = -1
        best_match_score = 0
        
        # Try to find the best matching disease from parsed results
        for i, found_disease in enumerate(found_diseases):
            # Check for exact match
            if original_lower == found_disease:
                best_match_idx = i
                best_match_score = 1.0
                break
            
            # Check for partial match (disease name contained in description or vice versa)
            if found_disease in original_lower or original_lower in found_disease:
                # Calculate match score based on length similarity
                score = min(len(found_disease), len(original_lower)) / max(len(found_disease), len(original_lower))
                if score > best_match_score:
                    best_match_score = score
                    best_match_idx = i
        
        if best_match_idx >= 0 and best_match_score > 0.5:  # Minimum 50% match
            final_classifications.append(parsed_classifications[best_match_idx])
            # Remove used classification to avoid double matching
            found_diseases.pop(best_match_idx)
            parsed_classifications.pop(best_match_idx)
        else:
            print(f"WARNING: Could not match original disease '{original_desc}' to any response")
            # Don't add anything - this will cause a length mismatch and trigger retry
    
    print(f"DEBUG: Successfully matched {len(final_classifications)} out of {len(original_descriptions)} diseases")
    
    return final_classifications

def csv_updater_worker(df, output_file, batch_size):
    """
    Worker thread that continuously updates the CSV file with new classifications
    """
    last_save_time = time.time()
    save_interval = 30  # Save every 30 seconds
    
    while not stop_flag.is_set():
        try:
            # Get update from queue (timeout to check stop_flag periodically)
            batch_index, classifications = update_queue.get(timeout=1)
            
            # Update the dataframe
            start_idx = batch_index * batch_size
            for i, classification in enumerate(classifications):
                if start_idx + i < len(df):
                    df.iloc[start_idx + i, df.columns.get_loc('classification')] = classification
            
            # Save to CSV periodically or when queue is processed
            current_time = time.time()
            if current_time - last_save_time > save_interval or update_queue.empty():
                df.to_csv(output_file, index=False)
                last_save_time = current_time
            
            update_queue.task_done()
            
        except:
            continue  # Timeout or other error, continue checking
    
    # Final save when stopping
    df.to_csv(output_file, index=False)

def signal_handler(signum, frame):
    """Handle Ctrl+C gracefully"""
    print("\nReceived interrupt signal. Saving progress and stopping...")
    stop_flag.set()
    sys.exit(0)

def process_csv_file_parallel(input_file, output_file, batch_size=50, max_workers=8):
    """
    Process the CSV file in parallel batches to classify diseases
    """
    try:
        # Read the CSV file
        df = pd.read_csv(input_file)
        print(f"Loaded {len(df)} records from {input_file}")
        
        # Add a classification column if it doesn't exist
        if 'classification' not in df.columns:
            df['classification'] = ""
        
        # Set up signal handler for graceful shutdown
        signal.signal(signal.SIGINT, signal_handler)
        
        # Start the CSV updater thread
        live_output_file = output_file.replace('.csv', '_live_updates.csv')
        updater_thread = threading.Thread(
            target=csv_updater_worker, 
            args=(df, live_output_file, batch_size),
            daemon=True
        )
        updater_thread.start()
        
        # Prepare batches
        batches = []
        for i in range(0, len(df), batch_size):
            batch_end = min(i + batch_size, len(df))
            batch_descriptions = df.iloc[i:batch_end]['description'].tolist()
            batches.append((i // batch_size, batch_descriptions))
        
        print(f"Processing {len(batches)} batches with {max_workers} workers...")
        print(f"Live updates will be saved to: {live_output_file}")
        
        # Process batches in parallel
        completed_batches = 0
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all batches
            future_to_batch = {
                executor.submit(classify_diseases_batch, batch_data): batch_data[0] 
                for batch_data in batches
            }
            
            # Process completed batches
            with tqdm(total=len(batches), desc="Processing batches") as pbar:
                for future in concurrent.futures.as_completed(future_to_batch):
                    if stop_flag.is_set():
                        break
                        
                    try:
                        batch_index, classifications = future.result()
                        
                        # Add to update queue for live CSV updates
                        update_queue.put((batch_index, classifications))
                        
                        completed_batches += 1
                        pbar.update(1)
                        pbar.set_postfix({
                            'completed': completed_batches,
                            'queue_size': update_queue.qsize()
                        })
                        
                    except Exception as e:
                        print(f"Batch {future_to_batch[future]} failed completely: {e}")
                        # Skip this batch - do not update the dataframe
                        pbar.update(1)
        
        # Wait for all updates to be processed
        print("Waiting for final updates to be saved...")
        update_queue.join()
        stop_flag.set()
        
        # Final save and analysis
        classified_file = input_file.replace('.csv', '_classified.csv')
        df.to_csv(classified_file, index=False)
        print(f"Full classified dataset saved to: {classified_file}")
        
        # Filter for common diseases only
        common_diseases = df[df['classification'] == 'common disease'].copy()
        common_diseases = common_diseases[['code', 'description']]
        common_diseases.to_csv(output_file, index=False)
        
        # Print summary including all classifications
        print(f"\nClassification Summary:")
        
        total_diseases = len(df)
        classification_counts = df['classification'].value_counts()
        print(f"Total entries: {total_diseases}")
        print("\nClassification breakdown:")
        print(classification_counts)
        
        # Calculate percentages
        for classification, count in classification_counts.items():
            percentage = count / total_diseases * 100
            print(f"{classification}: {percentage:.1f}%")
        
        # Filter for common diseases only (excluding invalid entries)
        common_diseases = df[df['classification'] == 'common disease'].copy()
        common_diseases = common_diseases[['code', 'description']]
        common_diseases.to_csv(output_file, index=False)
        
        # Also save all classified diseases (excluding invalid entries)
        valid_diseases = df[df['classification'] != 'not a valid entry'].copy()
        valid_output_file = output_file.replace('.csv', '_all_valid.csv')
        valid_diseases.to_csv(valid_output_file, index=False)
        
        print(f"\nCommon diseases ({len(common_diseases)} records) saved to: {output_file}")
        print(f"All valid diseases ({len(valid_diseases)} records) saved to: {valid_output_file}")
        
        valid_count = len(valid_diseases)
        if valid_count > 0:
            print(f"Common diseases as % of valid entries: {len(common_diseases)/valid_count*100:.1f}%")
        
        return df, common_diseases
        
    except FileNotFoundError:
        print(f"Error: File '{input_file}' not found.")
        return None, None
    except Exception as e:
        print(f"Error processing file: {e}")
        stop_flag.set()
        return None, None

def main():
    input_file = "diseases.csv"
    output_file = "classified_diseases.csv"
    batch_size = 50
    max_workers = 8
    
    print(f"Starting parallel processing with {max_workers} workers...")
    print("Press Ctrl+C to stop and save progress at any time")
    
    df, common_df = process_csv_file_parallel(input_file, output_file, batch_size, max_workers)
    
    if df is not None:
        print("\nSample of classifications:")
        sample_df = df[['description', 'classification']].head(10)
        for _, row in sample_df.iterrows():
            desc = row['description'][:50] if len(row['description']) > 50 else row['description']
            print(f"{desc:<50} -> {row['classification']}")
        
        print(f"\nProcessing complete! Check '{output_file.replace('.csv', '_live_updates.csv')}' for live updates during processing.")

if __name__ == "__main__":
    main()
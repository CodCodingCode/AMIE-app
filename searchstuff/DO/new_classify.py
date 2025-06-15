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

    1. common disease - frequent, everyday conditions like cold, flu, headache, minor infections, common bacterial/viral infections, common allergies
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
    <number>. <classification>

    Where <classification> is exactly one of: common disease, emergency disease, rare disease, mental disease, not a valid entry

    Example response:
    1. emergency disease
    2. common disease
    3. rare disease
    4. mental disease
    5. not a valid entry

    Respond with exactly {len(descriptions_batch)} lines, one for each entry in the same order as listed above.
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
            classifications = parse_disease_classification_response(response_text, len(descriptions_batch))
            
            if len(classifications) == len(descriptions_batch):
                return (batch_index, classifications)
            else:
                raise ValueError(f"Response mismatch: expected {len(descriptions_batch)} classifications, got {len(classifications)}")
                
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"Error with batch {batch_index}, attempt {attempt + 1}: {e}")
                time.sleep(2 ** attempt)
                continue
    
    # If all retries failed, return default classifications
    print(f"Batch {batch_index} failed after {max_retries} attempts. Using default 'common disease' classification.")
    return (batch_index, ["common disease"] * len(descriptions_batch))

def parse_disease_classification_response(response_text, expected_count):
    """
    Parse the numbered classification response from OpenAI.
    Returns a list of classifications in order.
    """
    valid_categories = ["common disease", "emergency disease", "rare disease", "mental disease", "not a valid entry"]
    
    # Split response into lines and clean them
    lines = [line.strip() for line in response_text.split('\n') if line.strip()]
    
    print(f"DEBUG: Found {len(lines)} response lines for {expected_count} diseases")
    
    # Parse each line looking for numbered format
    classifications = []
    
    for line in lines:
        # Look for pattern like "1. common disease" or "1. emergency disease"
        line_lower = line.lower()
        
        # Find which classification this line contains
        found_classification = None
        for category in valid_categories:
            if category in line_lower:
                found_classification = category
                break
        
        if found_classification:
            classifications.append(found_classification)
        else:
            print(f"WARNING: Could not parse classification from line: '{line}'")
    
    print(f"DEBUG: Successfully parsed {len(classifications)} out of {expected_count} classifications")
    
    # If we don't have enough classifications, pad with "common disease"
    while len(classifications) < expected_count:
        classifications.append("common disease")
        print(f"WARNING: Padding missing classification with 'common disease'")
    
    # If we have too many, truncate
    if len(classifications) > expected_count:
        classifications = classifications[:expected_count]
        print(f"WARNING: Truncating excess classifications")
    
    return classifications

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
                print(f"Progress saved: {sum(1 for x in df['classification'] if x)} / {len(df)} completed")
            
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

def process_csv_file_parallel(input_file, output_file, batch_size=10, max_workers=4):
    """
    Process the CSV file in parallel batches to classify diseases
    """
    try:
        # Read the CSV file
        df = pd.read_csv(input_file)
        print(f"Loaded {len(df)} records from {input_file}")
        
        # Check if the disease column exists (adjust column name as needed)
        disease_column = None
        if 'disease' in df.columns:
            disease_column = 'disease'
        elif 'description' in df.columns:
            disease_column = 'description'
        else:
            print("Error: No 'disease' or 'description' column found in CSV")
            return None, None
        
        print(f"Using column '{disease_column}' for disease descriptions")
        
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
            batch_descriptions = df.iloc[i:batch_end][disease_column].tolist()
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
        
        # Filter for common diseases only
        common_diseases = df[df['classification'] == 'common disease'].copy()
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
    batch_size = 10  # Smaller batches for better error handling
    max_workers = 4  # Reduced workers to avoid rate limits
    
    print(f"Starting parallel processing with {max_workers} workers...")
    print("Press Ctrl+C to stop and save progress at any time")
    
    df, common_df = process_csv_file_parallel(input_file, output_file, batch_size, max_workers)
    
    if df is not None:
        print("\nSample of classifications:")
        # Use the correct column name
        disease_col = 'disease' if 'disease' in df.columns else 'description'
        sample_df = df[[disease_col, 'classification']].head(10)
        for _, row in sample_df.iterrows():
            desc = row[disease_col][:50] if len(row[disease_col]) > 50 else row[disease_col]
            print(f"{desc:<50} -> {row['classification']}")
        
        print(f"\nProcessing complete! Check output files for results.")

if __name__ == "__main__":
    main()
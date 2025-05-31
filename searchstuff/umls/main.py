import requests
import pandas as pd
import time
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from typing import List, Dict, Tuple

# Your API key
API_KEY = "8da8b4db-38db-486c-9078-2587d19b9f6a"

# Thread-safe lock for file operations
file_lock = threading.Lock()

def get_concept_name(cui: str) -> str:
    """Get the main concept name"""
    url = f"https://uts-ws.nlm.nih.gov/rest/content/current/CUI/{cui}"
    params = {"apiKey": API_KEY}
    
    try:
        response = requests.get(url, params=params, timeout=30)
        if response.status_code == 200:
            data = response.json()
            return data.get('result', {}).get('name', '')
        return ''
    except Exception as e:
        print(f"    Error getting concept name for {cui}: {e}")
        return ''

def get_detailed_definitions(cui: str) -> List[str]:
    """Get detailed definitions for a single CUI"""
    url = f"https://uts-ws.nlm.nih.gov/rest/content/current/CUI/{cui}/definitions"
    params = {"apiKey": API_KEY, "pageSize": 100}
    
    try:
        response = requests.get(url, params=params, timeout=30)
        if response.status_code == 200:
            data = response.json()
            definitions = []
            
            for definition in data.get('result', []):
                value = definition.get('value', '')
                if value:  # Only include definitions with actual content
                    definitions.append(value)
            
            return definitions
        return []
    except Exception as e:
        print(f"    Error getting definitions for {cui}: {e}")
        return []

def process_single_cui(cui: str) -> Dict[str, str]:
    """Process a single CUI and return the result"""
    print(f"Processing CUI: {cui}")
    
    # Get concept name
    concept_name = get_concept_name(cui)
    print(f"  Concept: {concept_name}")
    
    # Get detailed definitions
    definitions = get_detailed_definitions(cui)
    print(f"  Found {len(definitions)} definitions for {cui}")
    
    # Combine all definitions into one string for this disease
    if definitions:
        # Join all definitions with double newline separator
        combined_definition = '\n\n'.join(definitions)
        result = {
            'cui': cui,
            'disease_name': concept_name,
            'definition': combined_definition
        }
    else:
        # Include concepts with no definitions for completeness
        result = {
            'cui': cui,
            'disease_name': concept_name,
            'definition': 'No detailed definition available'
        }
    
    # Small delay to be nice to the API
    time.sleep(0.05)  # Reduced since we're using multiple workers
    
    return result

def save_progress(results: List[Dict], filename: str = 'disease_definitions_progress.json'):
    """Thread-safe progress saving"""
    with file_lock:
        try:
            with open(filename, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"  Saved progress: {len(results)} diseases to {filename}")
        except Exception as e:
            print(f"  Error saving progress: {e}")

def process_cuis_parallel(csv_file: str, max_workers: int = 8) -> List[Dict]:
    """Process CUIs in parallel and return concept names with their detailed definitions"""
    # Read CSV
    df = pd.read_csv(csv_file)
    cuis = df['Concept_Unique_Identifier_1'].drop_duplicates().tolist()
    
    print(f"Starting parallel processing of {len(cuis)} CUIs with {max_workers} workers...")
    
    results = []
    completed_count = 0
    
    # Use ThreadPoolExecutor for parallel processing
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_cui = {executor.submit(process_single_cui, cui): cui for cui in cuis}
        
        # Process completed tasks as they finish
        for future in as_completed(future_to_cui):
            cui = future_to_cui[future]
            try:
                result = future.result()
                results.append(result)
                completed_count += 1
                
                print(f"Completed {completed_count}/{len(cuis)}: {result['disease_name']}")
                
                # Save progress every 10 completed tasks
                if completed_count % 10 == 0:
                    save_progress(results)
                
            except Exception as e:
                print(f"Error processing CUI {cui}: {e}")
                # Add a placeholder result for failed CUIs
                results.append({
                    'cui': cui,
                    'disease_name': f'Error processing {cui}',
                    'definition': f'Error occurred: {str(e)}'
                })
                completed_count += 1
    
    # Final progress save
    save_progress(results)
    
    # Sort results by CUI to maintain some consistency
    results.sort(key=lambda x: x['cui'])
    
    return results

def main():
    """Main execution function"""
    start_time = time.time()
    
    print("Starting parallel CUI processing...")
    results = process_cuis_parallel('onlyCUIs.csv', max_workers=8)
    
    # Prepare data for CSV (remove CUI column for final output)
    csv_results = [{'disease_name': r['disease_name'], 'definition': r['definition']} for r in results]
    
    # Save to CSV - just disease names and their detailed definitions
    df_output = pd.DataFrame(csv_results)
    df_output.to_csv('disease_definitions.csv', index=False)
    
    # Final save to JSON as well
    with open('disease_definitions_final.json', 'w') as f:
        json.dump(csv_results, f, indent=2)
    
    end_time = time.time()
    processing_time = end_time - start_time
    
    print(f"\nDone! Processed {len(results)} diseases in {processing_time:.2f} seconds.")
    print(f"Average time per CUI: {processing_time/len(results):.2f} seconds")
    print("Output saved to:")
    print("- disease_definitions.csv (CSV format)")
    print("- disease_definitions_final.json (final JSON)")
    print("- disease_definitions_progress.json (progress saves)")
    
    print("\nSample output:")
    for i, result in enumerate(csv_results[:3]):  # Show first 3 entries
        print(f"{i+1}. {result['disease_name']}")
        preview = result['definition'][:200] + "..." if len(result['definition']) > 200 else result['definition']
        print(f"   Definition: {preview}")
        print()

if __name__ == "__main__":
    main()
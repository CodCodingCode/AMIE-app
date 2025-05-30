import os
import csv
import json
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Any
from tavily import TavilyClient
from openai import OpenAI
import logging
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MedicalInfoSystem:
    def __init__(self):
        # Initialize API clients with backup keys
        self.tavily_keys = [
            "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",
            "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"
        ]
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        
        if not self.openai_api_key:
            raise ValueError("Please set OPENAI_API_KEY environment variable")
        
        # File paths
        self.disease_db_path = "filtered_diseases_10000.csv"
        self.results_csv_path = "medical_research_results.csv"
        self.results_json_path = "medical_research_results.json"
        
        # Thread-safe locks for file operations
        self.csv_lock = threading.Lock()
        self.json_lock = threading.Lock()
        
        # Initialize results storage
        self._initialize_storage()
    
    def _get_tavily_client(self, worker_id: int) -> TavilyClient:
        """Get a Tavily client with key rotation based on worker ID"""
        key_index = worker_id % len(self.tavily_keys)
        return TavilyClient(api_key=self.tavily_keys[key_index])
    
    def _get_openai_client(self) -> OpenAI:
        """Get an OpenAI client (thread-safe)"""
        return OpenAI(api_key=self.openai_api_key)
    
    def _initialize_storage(self):
        """Initialize CSV and JSON storage files if they don't exist"""
        csv_headers = [
            'disease_name', 'symptoms', 'causes', 'treatment_options', 
            'diagnosis_methods', 'risk_factors', 'prevention', 'prognosis', 
            'family_history_impact', 'hereditary_factors', 'genetic_risk_assessment'
        ]
        
        if not os.path.exists(self.results_csv_path):
            with open(self.results_csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(csv_headers)
        
        if not os.path.exists(self.results_json_path):
            with open(self.results_json_path, 'w', encoding='utf-8') as f:
                json.dump([], f, indent=2)
    
    def get_diseases_from_csv(self, limit: int = 1000) -> List[str]:
        """Extract disease names from the medical terminology CSV"""
        diseases = []
        
        try:
            logger.info(f"Reading diseases from {self.disease_db_path}...")
            
            chunk_size = 10000
            processed_terms = set()
            
            for chunk in pd.read_csv(self.disease_db_path, chunksize=chunk_size):
                for _, row in chunk.iterrows():
                    term = str(row.get('term', '')).strip()
                    
                    if term and len(term) > 3 and term not in processed_terms:
                        diseases.append(term)
                        processed_terms.add(term)
                    
                    if len(diseases) >= limit:
                        break
                
                if len(diseases) >= limit:
                    break
            
            logger.info(f"Found {len(diseases)} diseases")
            return diseases[:limit]
            
        except Exception as e:
            logger.error(f"Error reading diseases from CSV: {e}")
            return []
    
    def search_medical_info(self, disease: str, worker_id: int = 0) -> Dict[str, Any]:
        """Search for comprehensive medical information about a disease"""
        logger.info(f"Worker {worker_id}: Searching information for: {disease}")
        
        query = f"Medical information {disease}: symptoms causes treatment diagnosis risk factors prevention prognosis family history genetic hereditary"
        
        # Get clients for this worker
        tavily_client = self._get_tavily_client(worker_id)
        openai_client = self._get_openai_client()
        
        # Try with different Tavily keys if one fails
        for attempt in range(len(self.tavily_keys)):
            try:
                if attempt > 0:
                    # Switch to next key if previous attempt failed
                    key_index = (worker_id + attempt) % len(self.tavily_keys)
                    tavily_client = TavilyClient(api_key=self.tavily_keys[key_index])
                
                search_results = tavily_client.search(
                    query=query, 
                    search_depth="advanced", 
                    include_answer=False,
                    max_results=8
                )
                
                sources = []
                for result in search_results.get("results", [])[:6]:
                    sources.append({
                        'title': result.get('title', 'No title'),
                        'content': result.get('content', ''),
                        'url': result.get('url', ''),
                        'score': result.get('score', 0)
                    })
                
                sources_text = "\n\n".join([
                    f"Source {i+1}: {source['title']}\n{source['content']}"
                    for i, source in enumerate(sources)
                ])
                
                prompt = f"""Analyze these sources about {disease} and extract comprehensive medical information. Return a valid JSON object with this exact structure:

{{
    "disease_name": "{disease}",
    "symptoms": ["symptom1", "symptom2"],
    "causes": ["cause1", "cause2"],
    "treatment_options": ["treatment1", "treatment2"],
    "diagnosis_methods": ["method1", "method2"],
    "risk_factors": ["factor1", "factor2"],
    "prevention": ["prevention1", "prevention2"],
    "prognosis": "brief prognosis description",
    "family_history_impact": {{
        "inheritance_pattern": "inheritance description or 'Not specified'",
        "risk_increase": "family risk description or 'Not specified'",
        "age_of_onset_influence": "onset influence or 'Not specified'",
        "severity_influence": "severity influence or 'Not specified'",
        "screening_recommendations": "screening recommendations or 'Not specified'"
    }},
    "hereditary_factors": ["factor1", "factor2"],
    "genetic_risk_assessment": "genetic assessment summary"
}}

Sources:
{sources_text}

Extract only information present in the sources. Use "Not specified" for missing information. Focus on medical accuracy and completeness."""
                
                response = openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.2,
                )
                
                content = response.choices[0].message.content.strip()
                
                try:
                    start_idx = content.find('{')
                    end_idx = content.rfind('}') + 1
                    if start_idx != -1 and end_idx != 0:
                        json_str = content[start_idx:end_idx]
                        structured_info = json.loads(json_str)
                    else:
                        raise ValueError("No JSON found in response")
                except:
                    structured_info = {
                        "disease_name": disease,
                        "symptoms": [],
                        "causes": [],
                        "treatment_options": [],
                        "diagnosis_methods": [],
                        "risk_factors": [],
                        "prevention": [],
                        "prognosis": "Information processing failed",
                        "family_history_impact": {
                            "inheritance_pattern": "Not specified",
                            "risk_increase": "Not specified",
                            "age_of_onset_influence": "Not specified",
                            "severity_influence": "Not specified",
                            "screening_recommendations": "Not specified"
                        },
                        "hereditary_factors": [],
                        "genetic_risk_assessment": "Information processing failed"
                    }
                
                logger.info(f"Worker {worker_id}: Successfully processed information for {disease}")
                return structured_info
                
            except Exception as e:
                logger.error(f"Worker {worker_id}: Error with Tavily key attempt {attempt} for {disease}: {e}")
                if attempt < len(self.tavily_keys) - 1:
                    logger.info(f"Worker {worker_id}: Trying with next Tavily key...")
                else:
                    logger.error(f"Worker {worker_id}: All Tavily keys failed for {disease}")
                    return {
                        'disease_name': disease,
                        'error': str(e),
                        'worker_id': worker_id
                    }
    
    def save_to_csv(self, medical_info: Dict[str, Any]):
        """Thread-safe save medical information to CSV file"""
        try:
            with self.csv_lock:
                with open(self.results_csv_path, 'a', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    
                    family_history = medical_info.get('family_history_impact', {})
                    family_history_text = f"Inheritance: {family_history.get('inheritance_pattern', 'N/A')}; Risk: {family_history.get('risk_increase', 'N/A')}; Onset: {family_history.get('age_of_onset_influence', 'N/A')}; Severity: {family_history.get('severity_influence', 'N/A')}; Screening: {family_history.get('screening_recommendations', 'N/A')}"
                    
                    row = [
                        medical_info.get('disease_name', ''),
                        '; '.join(medical_info.get('symptoms', [])),
                        '; '.join(medical_info.get('causes', [])),
                        '; '.join(medical_info.get('treatment_options', [])),
                        '; '.join(medical_info.get('diagnosis_methods', [])),
                        '; '.join(medical_info.get('risk_factors', [])),
                        '; '.join(medical_info.get('prevention', [])),
                        medical_info.get('prognosis', ''),
                        family_history_text,
                        '; '.join(medical_info.get('hereditary_factors', [])),
                        medical_info.get('genetic_risk_assessment', '')
                    ]
                    
                    writer.writerow(row)
                    logger.info(f"Saved {medical_info.get('disease_name')} to CSV")
                    
        except Exception as e:
            logger.error(f"Error saving to CSV: {e}")
    
    def save_to_json(self, medical_info: Dict[str, Any]):
        """Thread-safe save medical information to JSON file"""
        try:
            with self.json_lock:
                with open(self.results_json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                data.append(medical_info)
                
                with open(self.results_json_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                logger.info(f"Saved {medical_info.get('disease_name')} to JSON")
                
        except Exception as e:
            logger.error(f"Error saving to JSON: {e}")
    
    def process_disease(self, disease: str, worker_id: int = 0) -> Dict[str, Any]:
        """Process a single disease: search, structure, and save information"""
        medical_info = self.search_medical_info(disease, worker_id)
        
        if 'error' not in medical_info:
            self.save_to_csv(medical_info)
            self.save_to_json(medical_info)
        
        return medical_info
    
    def process_diseases_worker(self, diseases: List[str], worker_id: int, progress_queue: Queue) -> List[Dict[str, Any]]:
        """Worker function to process a batch of diseases"""
        results = []
        
        for i, disease in enumerate(diseases):
            try:
                logger.info(f"Worker {worker_id}: Processing disease {i+1}/{len(diseases)}: {disease}")
                result = self.process_disease(disease, worker_id)
                results.append(result)
                
                # Update progress
                progress_queue.put(1)
                
                # Rate limiting - smaller delay since we have multiple workers
                time.sleep(0.2)
                
            except Exception as e:
                logger.error(f"Worker {worker_id}: Error processing {disease}: {e}")
                results.append({
                    'disease_name': disease,
                    'error': str(e),
                    'worker_id': worker_id
                })
                progress_queue.put(1)
        
        logger.info(f"Worker {worker_id}: Completed processing {len(results)} diseases")
        return results
    
    def process_all_diseases_parallel(self, num_workers: int = 8):
        """Process 1000 diseases with parallel processing using multiple workers"""
        diseases = self.get_diseases_from_csv(limit=1000)
        
        if not diseases:
            print("No diseases found in CSV")
            return
        
        print(f"Starting parallel processing of {len(diseases)} diseases with {num_workers} workers...")
        
        # Split diseases into chunks for each worker
        chunk_size = len(diseases) // num_workers
        disease_chunks = []
        
        for i in range(num_workers):
            start_idx = i * chunk_size
            if i == num_workers - 1:  # Last worker gets remaining diseases
                end_idx = len(diseases)
            else:
                end_idx = (i + 1) * chunk_size
            
            disease_chunks.append(diseases[start_idx:end_idx])
        
        # Progress tracking
        progress_queue = Queue()
        total_diseases = len(diseases)
        processed_count = 0
        
        def progress_monitor():
            nonlocal processed_count
            while processed_count < total_diseases:
                try:
                    progress_queue.get(timeout=1)
                    processed_count += 1
                    if processed_count % 10 == 0 or processed_count == total_diseases:
                        print(f"Progress: {processed_count}/{total_diseases} diseases processed ({processed_count/total_diseases*100:.1f}%)")
                except:
                    continue
        
        # Start progress monitor thread
        progress_thread = threading.Thread(target=progress_monitor, daemon=True)
        progress_thread.start()
        
        # Process diseases in parallel using ThreadPoolExecutor
        all_results = []
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            # Submit tasks for each worker
            future_to_worker = {
                executor.submit(self.process_diseases_worker, chunk, i, progress_queue): i 
                for i, chunk in enumerate(disease_chunks) if chunk
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_worker):
                worker_id = future_to_worker[future]
                try:
                    worker_results = future.result()
                    all_results.extend(worker_results)
                    logger.info(f"Worker {worker_id} completed successfully")
                except Exception as e:
                    logger.error(f"Worker {worker_id} failed with error: {e}")
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Wait for progress monitor to finish
        progress_thread.join(timeout=5)
        
        print(f"\nCompleted parallel processing:")
        print(f"- Total diseases processed: {len(all_results)}")
        print(f"- Processing time: {processing_time:.2f} seconds")
        print(f"- Average time per disease: {processing_time/len(all_results):.2f} seconds")
        print(f"- Results saved to: {self.results_csv_path} and {self.results_json_path}")
        
        # Count successful vs failed processing
        successful = sum(1 for result in all_results if 'error' not in result)
        failed = len(all_results) - successful
        print(f"- Successful: {successful}, Failed: {failed}")
        
        return all_results
    
    def process_all_diseases(self):
        """Process 1000 diseases automatically (legacy method - now calls parallel version)"""
        return self.process_all_diseases_parallel(num_workers=8)


def main():
    """Main function to run the medical information system with parallel processing"""
    try:
        system = MedicalInfoSystem()
        # Use parallel processing with 8 workers
        system.process_all_diseases_parallel(num_workers=8)
    
    except Exception as e:
        logger.error(f"Error in main: {e}")
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
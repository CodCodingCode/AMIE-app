import os
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
import asyncio
from crawl4ai import WebCrawler
from crawl4ai.extraction_strategy import LLMExtractionStrategy

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MedicalInfoSystem:
    def __init__(self):
        # Initialize API clients with backup keys
        self.tavily_keys = [
            "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",
            "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",
            "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",
            "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",
            "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",
            "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",
            "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",
        ]
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        
        if not self.openai_api_key:
            raise ValueError("Please set OPENAI_API_KEY environment variable")
        
        # File paths
        self.disease_db_path = "datasets/classified_diseases_cleaned2.csv"
        self.results_csv_path = "medical_research_results.csv"
        self.results_json_path = "medical_research_results.json"
        
        # Thread-safe locks for file operations
        self.csv_lock = threading.Lock()
        self.json_lock = threading.Lock()
        
        # Initialize results storage
        self._initialize_storage()
        
        # Initialize results dataframe for CSV operations
        self.results_df = pd.DataFrame()
        
        # Initialize web crawler
        self.crawler = None
    
    def _get_tavily_client(self, worker_id: int) -> TavilyClient:
        """Get a Tavily client with key rotation based on worker ID"""
        key_index = worker_id % len(self.tavily_keys)
        return TavilyClient(api_key=self.tavily_keys[key_index])
    
    def _get_openai_client(self) -> OpenAI:
        """Get an OpenAI client (thread-safe)"""
        return OpenAI(api_key=self.openai_api_key)
    
    def _initialize_crawler(self):
        """Initialize the web crawler for this worker"""
        if self.crawler is None:
            self.crawler = WebCrawler(
                # Enable JavaScript rendering for modern websites
                headless=True,
                browser_type="chromium",
                # Add stealth mode to avoid detection
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                # Optimize for medical content extraction
                extraction_strategy=LLMExtractionStrategy(
                    provider="openai/gpt-4o-mini",
                    api_token=self.openai_api_key,
                    instruction="Extract all medical content including symptoms, causes, treatments, diagnosis methods, risk factors, prevention, prognosis, and genetic/hereditary information. Focus on comprehensive medical information."
                )
            )
    
    def _initialize_storage(self):
        """Initialize CSV and JSON storage files if they don't exist"""
        # Initialize empty CSV with proper headers using pandas
        csv_columns = [
            'disease_name', 'symptoms', 'causes', 'treatment_options', 
            'diagnosis_methods', 'risk_factors', 'prevention', 'prognosis', 
            'inheritance_pattern', 'family_risk_increase', 'age_of_onset_influence',
            'severity_influence', 'screening_recommendations', 'hereditary_factors', 
            'genetic_risk_assessment', 'processing_timestamp'
        ]
        
        if not os.path.exists(self.results_csv_path):
            empty_df = pd.DataFrame(columns=csv_columns)
            empty_df.to_csv(self.results_csv_path, index=False)
            logger.info(f"Created CSV file with headers: {self.results_csv_path}")
        
        # Initialize empty JSON array
        if not os.path.exists(self.results_json_path):
            with open(self.results_json_path, 'w', encoding='utf-8') as f:
                json.dump([], f, indent=2)
            logger.info(f"Created JSON file: {self.results_json_path}")
    
    def get_diseases_from_csv(self, limit: int = None) -> List[str]:
        """Extract disease names from the medical terminology CSV"""
        diseases = []
        
        try:
            logger.info(f"Reading diseases from {self.disease_db_path}...")
            
            if not os.path.exists(self.disease_db_path):
                logger.error(f"Disease database file not found: {self.disease_db_path}")
                return []
            
            # Read CSV in chunks to handle large files
            chunk_size = 10000
            processed_terms = set()
            
            for chunk in pd.read_csv(self.disease_db_path, chunksize=chunk_size):
                # Try different possible column names for disease terms
                term_column = None
                for col in ['Title', 'title', 'term', 'disease', 'name', 'disease_name']:
                    if col in chunk.columns:
                        term_column = col
                        break
                
                if term_column is None:
                    # Use first column if no standard column found
                    term_column = chunk.columns[0]
                    logger.warning(f"Using first column '{term_column}' as disease terms")
                else:
                    logger.info(f"Using column '{term_column}' for disease terms")
                
                for _, row in chunk.iterrows():
                    term = str(row.get(term_column, '')).strip()
                    
                    # Filter valid disease terms
                    if (term and len(term) > 3 and 
                        term.lower() not in ['nan', 'null', 'none'] and 
                        term not in processed_terms):
                        diseases.append(term)
                        processed_terms.add(term)
                    
                    if limit and len(diseases) >= limit:
                        break
                
                if limit and len(diseases) >= limit:
                    break
            
            logger.info(f"Found {len(diseases)} unique diseases")
            return diseases[:limit] if limit else diseases
            
        except Exception as e:
            logger.error(f"Error reading diseases from CSV: {e}")
            return []
    
    async def crawl_website_content(self, url: str, worker_id: int = 0) -> str:
        """Crawl full content from a website URL using Crawl4AI"""
        try:
            # Initialize crawler if not done yet
            self._initialize_crawler()
            
            # Crawl the website with JavaScript rendering
            result = await self.crawler.arun(
                url=url,
                # Enable JavaScript execution for dynamic content
                js_code=["window.scrollTo(0, document.body.scrollHeight);"],
                # Wait for content to load
                wait_for="css:body",
                # Extract meaningful content
                extraction_strategy=LLMExtractionStrategy(
                    provider="openai/gpt-4o-mini",
                    api_token=self.openai_api_key,
                    instruction=f"Extract comprehensive medical information from this webpage. Focus on symptoms, causes, treatments, diagnosis, risk factors, prevention, prognosis, genetic factors, and hereditary information. Return clean, structured medical content."
                ),
                # Additional options for better extraction
                remove_overlay_elements=True,
                simulate_user=True,
                magic=True  # Enable advanced content extraction
            )
            
            if result.success:
                # Get the extracted content
                extracted_content = result.extracted_content
                
                # If extraction strategy worked, use that content
                if extracted_content:
                    content = str(extracted_content)
                else:
                    # Fallback to cleaned markdown content
                    content = result.markdown
                
                # Limit content length to avoid token limits
                if len(content) > 12000:
                    content = content[:12000] + "..."
                
                logger.info(f"Worker {worker_id}: Successfully crawled {len(content)} characters from {url}")
                return content
            else:
                logger.warning(f"Worker {worker_id}: Failed to crawl {url}: {result.error_message}")
                return ""
                
        except Exception as e:
            logger.warning(f"Worker {worker_id}: Failed to crawl content from {url}: {e}")
            return ""
    
    async def search_and_crawl_full_content(self, disease: str, worker_id: int = 0) -> Dict[str, Any]:
        """Search for websites and crawl their full content using Crawl4AI"""
        logger.info(f"Worker {worker_id}: Searching and crawling full content for: {disease}")
        
        # Multiple search queries for better coverage
        queries = [
            f"Medical information {disease}: symptoms causes treatment diagnosis risk factors prevention prognosis family history genetic hereditary",
            f"{disease} hereditary genetic family history inheritance pattern",
            f"{disease} clinical features symptoms treatment prognosis"
        ]
        
        all_website_contents = []
        
        # Get clients for this worker
        tavily_client = self._get_tavily_client(worker_id)
        openai_client = self._get_openai_client()
        
        # Try with different Tavily keys if one fails
        for attempt in range(min(3, len(self.tavily_keys))):
            try:
                if attempt > 0:
                    # Switch to next key if previous attempt failed
                    key_index = (worker_id + attempt) % len(self.tavily_keys)
                    tavily_client = TavilyClient(api_key=self.tavily_keys[key_index])
                
                # Perform searches to get website URLs
                all_urls = []
                for query in queries:  # Use all queries for comprehensive coverage
                    try:
                        search_results = tavily_client.search(
                            query=query, 
                            search_depth="advanced", 
                            include_answer=False,
                            max_results=5  # Get more URLs since crawling is more selective
                        )
                        
                        for result in search_results.get("results", []):
                            url = result.get('url', '')
                            if url and url not in all_urls:
                                all_urls.append(url)
                        
                        time.sleep(0.3)  # Brief delay between searches
                    except Exception as search_e:
                        logger.warning(f"Worker {worker_id}: Search failed for query '{query}': {search_e}")
                
                # Crawl full content from each website
                logger.info(f"Worker {worker_id}: Found {len(all_urls)} URLs, crawling full content...")
                
                crawl_tasks = []
                for i, url in enumerate(all_urls[:8]):  # Crawl up to 8 websites for comprehensive coverage
                    crawl_tasks.append(self.crawl_website_content(url, worker_id))
                
                # Execute crawling tasks concurrently
                crawled_contents = await asyncio.gather(*crawl_tasks, return_exceptions=True)
                
                # Process crawled results
                for i, content in enumerate(crawled_contents):
                    if isinstance(content, str) and content:
                        all_website_contents.append({
                            'url': all_urls[i],
                            'content': content,
                            'source_number': len(all_website_contents) + 1
                        })
                
                if not all_website_contents:
                    logger.warning(f"Worker {worker_id}: No website content crawled for {disease}")
                    raise ValueError("No website content could be crawled")
                
                # Combine all website contents
                combined_content = "\n\n" + "="*80 + "\n\n".join([
                    f"WEBSITE {content['source_number']}: {content['url']}\n\nCONTENT:\n{content['content']}"
                    for content in all_website_contents
                ])
                
                # Create prompt for GPT to analyze the full website contents
                prompt = f"""Analyze the following COMPLETE WEBSITE CONTENTS about {disease} and extract comprehensive medical information. These are full website pages crawled with JavaScript rendering, not just snippets. Return a valid JSON object with this exact structure:

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
        "inheritance_pattern": "inheritance description",
        "risk_increase": "family risk description",
        "age_of_onset_influence": "onset influence",
        "severity_influence": "severity influence",
        "screening_recommendations": "screening recommendations"
    }},
    "hereditary_factors": ["factor1", "factor2"],
    "genetic_risk_assessment": "genetic assessment summary"
}}

COMPLETE CRAWLED WEBSITE CONTENTS:
{combined_content}

INSTRUCTIONS:
1. Thoroughly analyze ALL the crawled website content provided above
2. Extract comprehensive and detailed information from the complete web pages
3. Use the extensive content to provide specific, detailed responses
4. For genetic/hereditary information, extract from the websites and supplement with medical knowledge
5. Provide specific, detailed responses rather than generic statements
6. If information is not available in the websites, use your medical training to provide accurate information
7. Do not leave any fields empty or use placeholder text
8. Focus on extracting detailed, specific information from the full crawled website content provided"""
                
                # Handle long prompts by truncating if necessary
                max_tokens = 150000  # Higher limit since crawled content is cleaner
                if len(prompt) > max_tokens:
                    logger.warning(f"Worker {worker_id}: Prompt too long ({len(prompt)} chars), truncating...")
                    truncated_content = combined_content[:max_tokens - 3000] + "\n\n[CONTENT TRUNCATED DUE TO LENGTH]"
                    prompt = prompt.replace(combined_content, truncated_content)
                
                response = openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.2,
                    max_tokens=2500
                )
                
                content = response.choices[0].message.content.strip()
                
                # Parse JSON response more robustly
                try:
                    # Find JSON boundaries
                    start_idx = content.find('{')
                    end_idx = content.rfind('}') + 1
                    
                    if start_idx != -1 and end_idx > start_idx:
                        json_str = content[start_idx:end_idx]
                        structured_info = json.loads(json_str)
                        
                        # Validate required fields
                        required_fields = ['disease_name', 'symptoms', 'causes', 'treatment_options']
                        if all(field in structured_info for field in required_fields):
                            structured_info['processing_timestamp'] = datetime.now().isoformat()
                            structured_info['websites_analyzed'] = len(all_website_contents)
                            structured_info['source_urls'] = [content['url'] for content in all_website_contents]
                            logger.info(f"Worker {worker_id}: Successfully processed {len(all_website_contents)} websites for {disease}")
                            return structured_info
                        else:
                            raise ValueError("Missing required fields in JSON response")
                    else:
                        raise ValueError("No valid JSON structure found in response")
                        
                except json.JSONDecodeError as je:
                    logger.error(f"Worker {worker_id}: JSON parsing error for {disease}: {je}")
                    raise ValueError(f"Invalid JSON response: {je}")
                
            except Exception as e:
                logger.error(f"Worker {worker_id}: Error with attempt {attempt} for {disease}: {e}")
                if attempt < min(2, len(self.tavily_keys) - 1):
                    logger.info(f"Worker {worker_id}: Trying with next approach...")
                    time.sleep(1)  # Brief delay before retry
                else:
                    logger.error(f"Worker {worker_id}: All attempts failed for {disease}")
        
        # Return error structure if all attempts failed
        return {
            'disease_name': disease,
            'error': f'Failed to process after {min(3, len(self.tavily_keys))} attempts',
            'worker_id': worker_id,
            'processing_timestamp': datetime.now().isoformat()
        }
    
    def save_to_csv(self, medical_info: Dict[str, Any]):
        """Thread-safe save medical information to CSV using pandas"""
        try:
            with self.csv_lock:
                # Prepare row data
                family_history = medical_info.get('family_history_impact', {})
                
                row_data = {
                    'disease_name': medical_info.get('disease_name', ''),
                    'symptoms': '; '.join(medical_info.get('symptoms', [])),
                    'causes': '; '.join(medical_info.get('causes', [])),
                    'treatment_options': '; '.join(medical_info.get('treatment_options', [])),
                    'diagnosis_methods': '; '.join(medical_info.get('diagnosis_methods', [])),
                    'risk_factors': '; '.join(medical_info.get('risk_factors', [])),
                    'prevention': '; '.join(medical_info.get('prevention', [])),
                    'prognosis': medical_info.get('prognosis', ''),
                    'inheritance_pattern': family_history.get('inheritance_pattern', ''),
                    'family_risk_increase': family_history.get('risk_increase', ''),
                    'age_of_onset_influence': family_history.get('age_of_onset_influence', ''),
                    'severity_influence': family_history.get('severity_influence', ''),
                    'screening_recommendations': family_history.get('screening_recommendations', ''),
                    'hereditary_factors': '; '.join(medical_info.get('hereditary_factors', [])),
                    'genetic_risk_assessment': medical_info.get('genetic_risk_assessment', ''),
                    'processing_timestamp': medical_info.get('processing_timestamp', datetime.now().isoformat())
                }
                
                # Create DataFrame from single row and append to CSV
                new_row_df = pd.DataFrame([row_data])
                
                # Append to existing CSV
                if os.path.exists(self.results_csv_path):
                    new_row_df.to_csv(self.results_csv_path, mode='a', header=False, index=False)
                else:
                    new_row_df.to_csv(self.results_csv_path, index=False)
                
                logger.info(f"Saved {medical_info.get('disease_name')} to CSV")
                    
        except Exception as e:
            logger.error(f"Error saving to CSV: {e}")
    
    def save_to_json(self, medical_info: Dict[str, Any]):
        """Thread-safe save medical information to JSON file"""
        try:
            with self.json_lock:
                # Read existing data
                if os.path.exists(self.results_json_path):
                    try:
                        with open(self.results_json_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                    except (json.JSONDecodeError, FileNotFoundError):
                        data = []
                else:
                    data = []
                
                # Add new entry
                data.append(medical_info)
                
                # Write back to file with proper formatting
                with open(self.results_json_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                logger.info(f"Saved {medical_info.get('disease_name')} to JSON")
                
        except Exception as e:
            logger.error(f"Error saving to JSON: {e}")
    
    def process_disease(self, disease: str, worker_id: int = 0) -> Dict[str, Any]:
        """Process a single disease: search websites, crawl full content, and extract information"""
        # Run the async crawling function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            medical_info = loop.run_until_complete(self.search_and_crawl_full_content(disease, worker_id))
        finally:
            loop.close()
        
        if 'error' not in medical_info:
            self.save_to_csv(medical_info)
            self.save_to_json(medical_info)
        else:
            logger.warning(f"Worker {worker_id}: Skipping save for {disease} due to processing error")
        
        return medical_info
    
    def process_diseases_worker(self, diseases: List[str], worker_id: int, progress_queue: Queue) -> List[Dict[str, Any]]:
        """Worker function to process a batch of diseases"""
        results = []
        
        logger.info(f"Worker {worker_id}: Starting to process {len(diseases)} diseases")
        
        for i, disease in enumerate(diseases):
            try:
                logger.info(f"Worker {worker_id}: Processing disease {i+1}/{len(diseases)}: {disease}")
                result = self.process_disease(disease, worker_id)
                results.append(result)
                
                # Update progress
                progress_queue.put(1)
                
                # Rate limiting - moderate delay since crawling is more efficient
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Worker {worker_id}: Error processing {disease}: {e}")
                error_result = {
                    'disease_name': disease,
                    'error': str(e),
                    'worker_id': worker_id,
                    'processing_timestamp': datetime.now().isoformat()
                }
                results.append(error_result)
                progress_queue.put(1)
        
        logger.info(f"Worker {worker_id}: Completed processing {len(results)} diseases")
        return results
    
    def process_all_diseases_parallel(self, num_workers: int = 8, limit: int = None):
        """Process diseases with parallel processing using multiple workers"""
        diseases = self.get_diseases_from_csv(limit=limit)
        
        if not diseases:
            print("No diseases found in CSV")
            return []
        
        limit_text = f" (limited to {limit})" if limit else ""
        print(f"Starting parallel processing of {len(diseases)} diseases{limit_text} with {num_workers} workers...")
        print("NOTE: Using Crawl4AI for comprehensive website crawling with JavaScript rendering")
        
        # Split diseases into chunks for each worker
        chunk_size = max(1, len(diseases) // num_workers)
        disease_chunks = []
        
        for i in range(0, len(diseases), chunk_size):
            chunk = diseases[i:i + chunk_size]
            if chunk:  # Only add non-empty chunks
                disease_chunks.append(chunk)
        
        # Adjust number of workers to actual chunks
        actual_workers = min(num_workers, len(disease_chunks))
        print(f"Using {actual_workers} workers for {len(disease_chunks)} chunks")
        
        # Progress tracking
        progress_queue = Queue()
        total_diseases = len(diseases)
        processed_count = 0
        
        def progress_monitor():
            nonlocal processed_count
            while processed_count < total_diseases:
                try:
                    progress_queue.get(timeout=10)
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
        
        with ThreadPoolExecutor(max_workers=actual_workers) as executor:
            # Submit tasks for each worker
            future_to_worker = {
                executor.submit(self.process_diseases_worker, chunk, i, progress_queue): i 
                for i, chunk in enumerate(disease_chunks)
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_worker):
                worker_id = future_to_worker[future]
                try:
                    worker_results = future.result()
                    all_results.extend(worker_results)
                    logger.info(f"Worker {worker_id} completed successfully with {len(worker_results)} results")
                except Exception as e:
                    logger.error(f"Worker {worker_id} failed with error: {e}")
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Wait for progress monitor to finish
        progress_thread.join(timeout=5)
        
        # Final summary
        successful = sum(1 for result in all_results if 'error' not in result)
        failed = len(all_results) - successful
        
        print(f"\n{'='*60}")
        print(f"PROCESSING COMPLETE")
        print(f"{'='*60}")
        print(f"Total diseases processed: {len(all_results)}")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")
        print(f"Processing time: {processing_time:.2f} seconds")
        print(f"Average time per disease: {processing_time/len(all_results):.2f} seconds")
        print(f"Results saved to:")
        print(f"  - CSV: {self.results_csv_path}")
        print(f"  - JSON: {self.results_json_path}")
        
        return all_results
    
    def process_all_diseases(self, limit: int = None):
        """Process diseases automatically (calls parallel version)"""
        return self.process_all_diseases_parallel(num_workers=8, limit=limit)


def main():
    """Main function to run the medical information system with Crawl4AI"""
    try:
        system = MedicalInfoSystem()
        # Process all diseases with 8 workers and no limit
        results = system.process_all_diseases_parallel(num_workers=8, limit=None)
        
        if results:
            print(f"\nProcessing completed. Check the output files for results.")
        else:
            print("No results were generated. Check the logs for errors.")
    
    except Exception as e:
        logger.error(f"Error in main: {e}")
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
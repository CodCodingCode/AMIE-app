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
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode, LLMConfig
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from pydantic import BaseModel, Field

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define the medical information schema using Pydantic
class FamilyHistoryImpact(BaseModel):
    inheritance_pattern: str = Field(description="How the disease is inherited (autosomal dominant, recessive, X-linked, etc.)")
    risk_increase: str = Field(description="How family history increases risk")
    age_of_onset_influence: str = Field(description="How family history affects age of onset")
    severity_influence: str = Field(description="How family history affects disease severity")
    screening_recommendations: str = Field(description="Screening recommendations for family members")

class MedicalInformation(BaseModel):
    disease_name: str = Field(description="Name of the disease")
    symptoms: List[str] = Field(description="List of symptoms and signs")
    causes: List[str] = Field(description="List of causes and risk factors")
    treatment_options: List[str] = Field(description="List of treatment options")
    diagnosis_methods: List[str] = Field(description="List of diagnostic methods and tests")
    risk_factors: List[str] = Field(description="List of risk factors")
    prevention: List[str] = Field(description="List of prevention methods")
    prognosis: str = Field(description="Overall prognosis and outcome expectations")
    family_history_impact: FamilyHistoryImpact = Field(description="Impact of family history on the disease")
    hereditary_factors: List[str] = Field(description="List of hereditary and genetic factors")
    genetic_risk_assessment: str = Field(description="Overall genetic risk assessment")

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
        ]
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        
        if not self.openai_api_key:
            raise ValueError("Please set OPENAI_API_KEY environment variable")
        
        # File paths
        self.disease_db_path = "datasets/balanced_diseases_sample2.csv"
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
    
    def _get_browser_config(self) -> BrowserConfig:
        """Get browser configuration for Crawl4AI"""
        return BrowserConfig(
            headless=True,
            browser_type="chromium",
            viewport_width=1280,
            viewport_height=720,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            java_script_enabled=True,
            verbose=False
        )
    
    def _get_llm_extraction_strategy(self, disease: str) -> LLMExtractionStrategy:
        """Get LLM extraction strategy with medical schema"""
        return LLMExtractionStrategy(
            llm_config=LLMConfig(
                provider="openai/gpt-4o-mini",
                api_token=self.openai_api_key
            ),
            schema=MedicalInformation.model_json_schema(),
            extraction_type="schema",
            instruction=f"""Extract comprehensive medical information about {disease} from the website content. 

Focus on:
1. All symptoms and clinical signs
2. Underlying causes and etiology  
3. Available treatment options (medications, procedures, lifestyle changes)
4. Diagnostic methods and tests used
5. Known risk factors
6. Prevention strategies
7. Prognosis and outcomes
8. Genetic and hereditary aspects
9. Family history implications
10. Screening recommendations for relatives

Be thorough and extract specific, detailed information. If certain information is not available, use your medical knowledge to provide accurate information for the field.""",
            chunk_token_threshold=8000,
            overlap_rate=0.1,
            apply_chunking=True,
            verbose=False
        )
    
    def _get_crawler_config(self, disease: str) -> CrawlerRunConfig:
        """Get crawler run configuration with LLM extraction"""
        return CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            word_count_threshold=100,
            excluded_tags=['nav', 'footer', 'header', 'aside', 'script', 'style', 'advertisement'],
            exclude_external_links=True,
            process_iframes=True,
            remove_overlay_elements=True,
            extraction_strategy=self._get_llm_extraction_strategy(disease),
            screenshot=False,
            pdf=False,
            verbose=False
        )
    
    def _initialize_storage(self):
        """Initialize CSV and JSON storage files if they don't exist"""
        csv_columns = [
            'disease_name', 'symptoms', 'causes', 'treatment_options', 
            'diagnosis_methods', 'risk_factors', 'prevention', 'prognosis', 
            'inheritance_pattern', 'family_risk_increase', 'age_of_onset_influence',
            'severity_influence', 'screening_recommendations', 'hereditary_factors', 
            'genetic_risk_assessment', 'processing_timestamp', 'websites_crawled', 'source_urls'
        ]
        
        if not os.path.exists(self.results_csv_path):
            empty_df = pd.DataFrame(columns=csv_columns)
            empty_df.to_csv(self.results_csv_path, index=False)
            logger.info(f"Created CSV file with headers: {self.results_csv_path}")
        
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
            
            chunk_size = 10000
            processed_terms = set()
            
            for chunk in pd.read_csv(self.disease_db_path, chunksize=chunk_size):
                term_column = None
                for col in ['Title', 'title', 'term', 'disease', 'name', 'disease_name']:
                    if col in chunk.columns:
                        term_column = col
                        break
                
                if term_column is None:
                    term_column = chunk.columns[0]
                    logger.warning(f"Using first column '{term_column}' as disease terms")
                else:
                    logger.info(f"Using column '{term_column}' for disease terms")
                
                for _, row in chunk.iterrows():
                    term = str(row.get(term_column, '')).strip()
                    
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
    
    async def search_medical_websites(self, disease: str, worker_id: int = 0) -> List[str]:
        """Search for medical websites about the disease"""
        try:
            tavily_client = self._get_tavily_client(worker_id)
            
            # Single comprehensive search query
            queries = [
                f"Medical information {disease}: symptoms causes treatment diagnosis risk factors prevention prognosis genetic hereditary family history inheritance screening"
            ]
            
            all_urls = []
            
            for query in queries:
                try:
                    search_results = tavily_client.search(
                        query=query, 
                        search_depth="advanced", 
                        include_answer=False,
                        max_results=8  # More results since we have only 1 query
                    )
                    
                    for result in search_results.get("results", []):
                        url = result.get('url', '')
                        if url and url not in all_urls:
                            all_urls.append(url)
                    
                    time.sleep(0.2)  # Brief delay between searches
                    
                except Exception as search_e:
                    logger.warning(f"Worker {worker_id}: Search failed for query '{query}': {search_e}")
            
            logger.info(f"Worker {worker_id}: Found {len(all_urls)} URLs for {disease}")
            return all_urls[:12]  # Return up to 12 URLs for comprehensive coverage
            
        except Exception as e:
            logger.error(f"Worker {worker_id}: Error searching for {disease}: {e}")
            return []
    
    async def crawl_multiple_websites(self, disease: str, urls: List[str], worker_id: int = 0) -> Dict[str, Any]:
        """Crawl multiple websites and extract medical information using Crawl4AI's built-in LLM"""
        if not urls:
            return {'error': 'No URLs to crawl', 'disease_name': disease}
        
        browser_config = self._get_browser_config()
        crawler_config = self._get_crawler_config(disease)
        
        all_extracted_data = []
        successful_urls = []
        
        async with AsyncWebCrawler(config=browser_config) as crawler:
            # Crawl each website with LLM extraction
            for i, url in enumerate(urls):
                try:
                    logger.info(f"Worker {worker_id}: Crawling website {i+1}/{len(urls)}: {url}")
                    
                    result = await crawler.arun(
                        url=url,
                        config=crawler_config
                    )
                    
                    if result.success and result.extracted_content:
                        try:
                            # Parse the JSON string from Crawl4AI
                            if isinstance(result.extracted_content, str):
                                json_data = json.loads(result.extracted_content)
                                
                                if isinstance(json_data, list):
                                    # Find the first non-error object with medical data
                                    extracted_data = None
                                    for item in json_data:
                                        if isinstance(item, dict) and item.get('error') != True and 'disease_name' in item:
                                            extracted_data = item
                                            break
                                    
                                    if extracted_data is None:
                                        logger.warning(f"Worker {worker_id}: No valid medical data found in extraction results from {url}")
                                        continue
                                        
                                elif isinstance(json_data, dict):
                                    extracted_data = json_data
                                else:
                                    logger.warning(f"Worker {worker_id}: Unexpected JSON structure from {url}: {type(json_data)}")
                                    continue
                            else:
                                logger.warning(f"Worker {worker_id}: Unexpected content type from {url}: {type(result.extracted_content)}")
                                continue
                            
                            all_extracted_data.append(extracted_data)
                            successful_urls.append(url)
                            
                            logger.info(f"Worker {worker_id}: Successfully extracted data from {url}")
                            
                        except (json.JSONDecodeError, KeyError, TypeError) as e:
                            logger.warning(f"Worker {worker_id}: Data parsing error for {url}: {e}")
                    else:
                        logger.warning(f"Worker {worker_id}: Failed to crawl or extract from {url}")
                    
                    # Brief delay between crawls
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    logger.warning(f"Worker {worker_id}: Error crawling {url}: {e}")
        
        if not all_extracted_data:
            return {'error': 'No data extracted from any website', 'disease_name': disease}
        
        # Combine data from multiple websites
        combined_data = self._combine_extracted_data(disease, all_extracted_data, successful_urls)
        logger.info(f"Worker {worker_id}: Successfully combined data from {len(successful_urls)} websites for {disease}")
        
        return combined_data
    
    def _combine_extracted_data(self, disease: str, extracted_data_list: List[Dict], urls: List[str]) -> Dict[str, Any]:
        """Combine medical information from multiple websites"""
        combined = {
            'disease_name': disease,
            'symptoms': [],
            'causes': [],
            'treatment_options': [],
            'diagnosis_methods': [],
            'risk_factors': [],
            'prevention': [],
            'prognosis': '',
            'family_history_impact': {
                'inheritance_pattern': '',
                'risk_increase': '',
                'age_of_onset_influence': '',
                'severity_influence': '',
                'screening_recommendations': ''
            },
            'hereditary_factors': [],
            'genetic_risk_assessment': '',
            'processing_timestamp': datetime.now().isoformat(),
            'websites_crawled': len(urls),
            'source_urls': urls
        }
        
        # Combine lists from all sources (removing duplicates)
        list_fields = ['symptoms', 'causes', 'treatment_options', 'diagnosis_methods', 'risk_factors', 'prevention', 'hereditary_factors']
        
        for data in extracted_data_list:
            for field in list_fields:
                if field in data and isinstance(data[field], list):
                    for item in data[field]:
                        if item and item not in combined[field]:
                            combined[field].append(item)
        
        # Combine text fields (take the most comprehensive one)
        text_fields = ['prognosis', 'genetic_risk_assessment']
        for field in text_fields:
            longest_text = ''
            for data in extracted_data_list:
                if field in data and isinstance(data[field], str) and len(data[field]) > len(longest_text):
                    longest_text = data[field]
            combined[field] = longest_text
        
        # Combine family history impact (take the most complete)
        family_history_fields = ['inheritance_pattern', 'risk_increase', 'age_of_onset_influence', 'severity_influence', 'screening_recommendations']
        for field in family_history_fields:
            longest_text = ''
            for data in extracted_data_list:
                if ('family_history_impact' in data and 
                    isinstance(data['family_history_impact'], dict) and 
                    field in data['family_history_impact'] and
                    len(str(data['family_history_impact'][field])) > len(longest_text)):
                    longest_text = str(data['family_history_impact'][field])
            combined['family_history_impact'][field] = longest_text
        
        return combined
    
    async def search_and_crawl_multiple_sites(self, disease: str, worker_id: int = 0) -> Dict[str, Any]:
        """Complete workflow: search for websites and crawl multiple sites with built-in LLM extraction"""
        logger.info(f"Worker {worker_id}: Processing {disease} with multiple website crawling")
        
        # Try with different Tavily keys if one fails
        for attempt in range(min(3, len(self.tavily_keys))):
            try:
                if attempt > 0:
                    key_index = (worker_id + attempt) % len(self.tavily_keys)
                    logger.info(f"Worker {worker_id}: Trying with Tavily key {key_index}")
                
                # Step 1: Search for medical websites
                urls = await self.search_medical_websites(disease, worker_id)
                
                if not urls:
                    raise ValueError("No URLs found in search")
                
                # Step 2: Crawl multiple websites with built-in LLM extraction
                result = await self.crawl_multiple_websites(disease, urls, worker_id)
                
                if 'error' not in result:
                    return result
                else:
                    raise ValueError(result['error'])
                
            except Exception as e:
                logger.error(f"Worker {worker_id}: Attempt {attempt + 1} failed for {disease}: {e}")
                if attempt < min(2, len(self.tavily_keys) - 1):
                    logger.info(f"Worker {worker_id}: Retrying with next approach...")
                    await asyncio.sleep(1)
                else:
                    logger.error(f"Worker {worker_id}: All attempts failed for {disease}")
        
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
                    'processing_timestamp': medical_info.get('processing_timestamp', datetime.now().isoformat()),
                    'websites_crawled': medical_info.get('websites_crawled', 0),
                    'source_urls': '; '.join(medical_info.get('source_urls', []))
                }
                
                new_row_df = pd.DataFrame([row_data])
                
                if os.path.exists(self.results_csv_path):
                    new_row_df.to_csv(self.results_csv_path, mode='a', header=False, index=False)
                else:
                    new_row_df.to_csv(self.results_csv_path, index=False)
                
                logger.info(f"Saved {medical_info.get('disease_name')} to CSV ({medical_info.get('websites_crawled', 0)} websites)")
                    
        except Exception as e:
            logger.error(f"Error saving to CSV: {e}")
    
    def save_to_json(self, medical_info: Dict[str, Any]):
        """Thread-safe save medical information to JSON file"""
        try:
            with self.json_lock:
                if os.path.exists(self.results_json_path):
                    try:
                        with open(self.results_json_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                    except (json.JSONDecodeError, FileNotFoundError):
                        data = []
                else:
                    data = []
                
                data.append(medical_info)
                
                with open(self.results_json_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                logger.info(f"Saved {medical_info.get('disease_name')} to JSON")
                
        except Exception as e:
            logger.error(f"Error saving to JSON: {e}")
    
    def process_disease(self, disease: str, worker_id: int = 0) -> Dict[str, Any]:
        """Process a single disease: search multiple websites and extract information with built-in LLM"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            medical_info = loop.run_until_complete(self.search_and_crawl_multiple_sites(disease, worker_id))
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
                
                progress_queue.put(1)
                time.sleep(0.3)  # Rate limiting
                
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
        print("NOTE: Using Crawl4AI's built-in LLM extraction with multiple website crawling per disease")
        
        chunk_size = max(1, len(diseases) // num_workers)
        disease_chunks = []
        
        for i in range(0, len(diseases), chunk_size):
            chunk = diseases[i:i + chunk_size]
            if chunk:
                disease_chunks.append(chunk)
        
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
        
        progress_thread = threading.Thread(target=progress_monitor, daemon=True)
        progress_thread.start()
        
        all_results = []
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=actual_workers) as executor:
            future_to_worker = {
                executor.submit(self.process_diseases_worker, chunk, i, progress_queue): i 
                for i, chunk in enumerate(disease_chunks)
            }
            
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
        progress_thread.join(timeout=5)
        
        # Final summary
        successful = sum(1 for result in all_results if 'error' not in result)
        failed = len(all_results) - successful
        total_websites = sum(result.get('websites_crawled', 0) for result in all_results if 'error' not in result)
        
        print(f"\n{'='*60}")
        print(f"PROCESSING COMPLETE")
        print(f"{'='*60}")
        print(f"Total diseases processed: {len(all_results)}")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")
        print(f"Total websites crawled: {total_websites}")
        print(f"Average websites per disease: {total_websites/successful if successful > 0 else 0:.1f}")
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
    """Main function to run the medical information system"""
    try:
        system = MedicalInfoSystem()
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
import os
import json
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from tavily import TavilyClient
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

class TestMultipleSitesLLM:
    def __init__(self):
        self.tavily_keys = [
            "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",
            "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",
            "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",
        ]
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        
        if not self.openai_api_key:
            raise ValueError("Please set OPENAI_API_KEY environment variable")
    
    def _get_tavily_client(self) -> TavilyClient:
        """Get a Tavily client"""
        return TavilyClient(api_key=self.tavily_keys[0])
    
    def _get_browser_config(self) -> BrowserConfig:
        """Get browser configuration for Crawl4AI"""
        return BrowserConfig(
            headless=True,
            browser_type="chromium",
            viewport_width=1280,
            viewport_height=720,
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
    
    async def test_search_multiple_sites(self, disease: str = "diabetes") -> List[str]:
        """Test searching for multiple medical websites"""
        logger.info(f"🔍 Testing multi-site search for: {disease}")
        
        try:
            tavily_client = self._get_tavily_client()
            
            # Optimized search queries - focused and comprehensive
            queries = [
                f"Medical information {disease}: symptoms causes treatment diagnosis risk factors prevention prognosis",
                f"{disease} hereditary genetic family history inheritance pattern screening"
            ]
            
            all_urls = []
            
            for i, query in enumerate(queries):
                try:
                    logger.info(f"  Query {i+1}/{len(queries)}: {query}")
                    
                    search_results = tavily_client.search(
                        query=query, 
                        search_depth="advanced", 
                        include_answer=False,
                        max_results=6  # Increased since we have fewer queries
                    )
                    
                    query_urls = []
                    for result in search_results.get("results", []):
                        url = result.get('url', '')
                        if url and url not in all_urls:
                            all_urls.append(url)
                            query_urls.append(url)
                    
                    logger.info(f"    Found {len(query_urls)} new URLs")
                    for url in query_urls:
                        logger.info(f"      - {url}")
                    
                except Exception as e:
                    logger.warning(f"    Search failed: {e}")
            
            logger.info(f"✅ Total unique URLs found: {len(all_urls)}")
            return all_urls[:8]  # Limit to 8 for testing
            
        except Exception as e:
            logger.error(f"❌ Search failed: {e}")
            return []
    
    async def test_crawl_with_built_in_llm(self, disease: str, urls: List[str]) -> Dict[str, Any]:
        """Test crawling multiple sites with Crawl4AI's built-in LLM extraction"""
        if not urls:
            return {'error': 'No URLs to test'}
        
        logger.info(f"🕷️ Testing multi-site crawling with built-in LLM for: {disease}")
        logger.info(f"   Will crawl {len(urls)} websites...")
        
        browser_config = self._get_browser_config()
        extraction_strategy = self._get_llm_extraction_strategy(disease)
        
        crawler_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            word_count_threshold=100,
            excluded_tags=['nav', 'footer', 'header', 'aside', 'script', 'style'],
            extraction_strategy=extraction_strategy,
            verbose=False
        )
        
        all_extracted_data = []
        successful_urls = []
        
        async with AsyncWebCrawler(config=browser_config) as crawler:
            for i, url in enumerate(urls):
                try:
                    logger.info(f"  🌐 Crawling site {i+1}/{len(urls)}: {url}")
                    
                    start_time = asyncio.get_event_loop().time()
                    
                    result = await crawler.arun(
                        url=url,
                        config=crawler_config
                    )
                    
                    end_time = asyncio.get_event_loop().time()
                    crawl_time = end_time - start_time
                    
                    if result.success:
                        logger.info(f"    ✅ Crawl successful ({crawl_time:.1f}s)")
                        logger.info(f"    📄 Content length: {len(result.markdown)} chars")
                        
                        if result.extracted_content:
                            try:
                                # CORRECTED PARSING LOGIC - This is the key fix!
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
                                            logger.warning(f"    ⚠️ No valid medical data found in extraction results")
                                            continue
                                            
                                    elif isinstance(json_data, dict):
                                        extracted_data = json_data
                                    else:
                                        logger.warning(f"    ⚠️ Unexpected JSON structure: {type(json_data)}")
                                        continue
                                else:
                                    logger.warning(f"    ⚠️ Unexpected content type: {type(result.extracted_content)}")
                                    continue
                                
                                all_extracted_data.append(extracted_data)
                                successful_urls.append(url)
                                
                                # Log what was extracted
                                symptoms_count = len(extracted_data.get('symptoms', []))
                                causes_count = len(extracted_data.get('causes', []))
                                treatments_count = len(extracted_data.get('treatment_options', []))
                                
                                logger.info(f"    🧠 LLM extraction successful:")
                                logger.info(f"      - Symptoms: {symptoms_count}")
                                logger.info(f"      - Causes: {causes_count}")
                                logger.info(f"      - Treatments: {treatments_count}")
                                
                            except (json.JSONDecodeError, KeyError, TypeError) as e:
                                logger.warning(f"    ⚠️ Data parsing error for {url}: {e}")
                        else:
                            logger.warning(f"    ⚠️ No extracted content from LLM")
                    else:
                        logger.warning(f"    ❌ Crawl failed: {result.error_message}")
                    
                    # Brief delay between crawls
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    logger.error(f"    ❌ Error crawling {url}: {e}")
        
        logger.info(f"🎯 Crawling complete: {len(successful_urls)}/{len(urls)} sites successful")
        
        if not all_extracted_data:
            return {'error': 'No data extracted from any website', 'disease_name': disease}
        
        # Combine data from multiple websites
        combined_data = self._combine_extracted_data(disease, all_extracted_data, successful_urls)
        return combined_data
    
    def _combine_extracted_data(self, disease: str, extracted_data_list: List[Dict], urls: List[str]) -> Dict[str, Any]:
        """Combine medical information from multiple websites"""
        logger.info(f"🔧 Combining data from {len(extracted_data_list)} sources...")
        
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
        
        # Log the combined results
        logger.info("📊 Combined extraction results:")
        logger.info(f"  - Total symptoms: {len(combined['symptoms'])}")
        logger.info(f"  - Total causes: {len(combined['causes'])}")
        logger.info(f"  - Total treatments: {len(combined['treatment_options'])}")
        logger.info(f"  - Total diagnosis methods: {len(combined['diagnosis_methods'])}")
        logger.info(f"  - Total risk factors: {len(combined['risk_factors'])}")
        logger.info(f"  - Total prevention methods: {len(combined['prevention'])}")
        logger.info(f"  - Hereditary factors: {len(combined['hereditary_factors'])}")
        
        return combined
    
    async def run_comprehensive_test(self, test_disease: str = "diabetes"):
        """Run comprehensive test of the new multi-site + built-in LLM system"""
        logger.info("="*70)
        logger.info("🧪 TESTING MULTIPLE SITES + BUILT-IN LLM EXTRACTION")
        logger.info("="*70)
        
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Test 1: Multi-site search
            logger.info(f"\n📋 Test 1: Searching for multiple medical websites about '{test_disease}'")
            urls = await self.test_search_multiple_sites(test_disease)
            
            if not urls:
                logger.error("❌ No URLs found - test failed")
                return False
            
            # Test 2: Multi-site crawling with built-in LLM
            logger.info(f"\n📋 Test 2: Crawling {len(urls)} sites with Crawl4AI's built-in LLM extraction")
            result = await self.test_crawl_with_built_in_llm(test_disease, urls)
            
            if 'error' in result:
                logger.error(f"❌ Crawling failed: {result['error']}")
                return False
            
            # Test 3: Analyze results
            logger.info(f"\n📋 Test 3: Analyzing combined results")
            
            total_time = asyncio.get_event_loop().time() - start_time
            
            # Save test results
            test_output = {
                'test_disease': test_disease,
                'test_timestamp': datetime.now().isoformat(),
                'total_websites_found': len(urls),
                'successful_extractions': result.get('websites_crawled', 0),
                'processing_time_seconds': round(total_time, 2),
                'extracted_data': result
            }
            
            with open('test_multiple_sites_results.json', 'w') as f:
                json.dump(test_output, f, indent=2)
            
            # Final summary
            logger.info("\n" + "="*70)
            logger.info("🎉 TEST RESULTS SUMMARY")
            logger.info("="*70)
            logger.info(f"✅ Test Disease: {test_disease}")
            logger.info(f"✅ Websites Found: {len(urls)}")
            logger.info(f"✅ Successful Extractions: {result.get('websites_crawled', 0)}")
            logger.info(f"✅ Total Processing Time: {total_time:.1f} seconds")
            logger.info(f"✅ Average Time per Site: {total_time/len(urls):.1f} seconds")
            
            logger.info(f"\n📈 EXTRACTED MEDICAL DATA:")
            logger.info(f"   • Symptoms: {len(result.get('symptoms', []))}")
            logger.info(f"   • Causes: {len(result.get('causes', []))}")
            logger.info(f"   • Treatments: {len(result.get('treatment_options', []))}")
            logger.info(f"   • Diagnosis Methods: {len(result.get('diagnosis_methods', []))}")
            logger.info(f"   • Risk Factors: {len(result.get('risk_factors', []))}")
            logger.info(f"   • Prevention: {len(result.get('prevention', []))}")
            logger.info(f"   • Hereditary Factors: {len(result.get('hereditary_factors', []))}")
            
            logger.info(f"\n💾 Test results saved to: test_multiple_sites_results.json")
            
            # Show sample data
            if result.get('symptoms'):
                logger.info(f"\n🔍 Sample Symptoms Found:")
                for i, symptom in enumerate(result['symptoms'][:3]):
                    logger.info(f"   {i+1}. {symptom}")
            
            if result.get('treatment_options'):
                logger.info(f"\n💊 Sample Treatments Found:")
                for i, treatment in enumerate(result['treatment_options'][:3]):
                    logger.info(f"   {i+1}. {treatment}")
            
            logger.info("\n✅ COMPREHENSIVE TEST PASSED!")
            logger.info("🚀 The new multi-site + built-in LLM system is working perfectly!")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Test failed with error: {e}")
            return False


async def main():
    """Run the comprehensive test"""
    try:
        tester = TestMultipleSitesLLM()
        
        # Test with diabetes first
        success = await tester.run_comprehensive_test("diabetes")
        
        if success:
            print("\n🎯 Want to test another disease? The system is ready!")
            print("🚀 You can now run the full medical_info_system.py on your entire dataset!")
        else:
            print("\n❌ Test failed. Please check the logs above for issues.")
            
    except Exception as e:
        logger.error(f"Test runner failed: {e}")
        print(f"\n❌ Test runner error: {e}")


if __name__ == "__main__":
    # Check environment
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Please set your OPENAI_API_KEY environment variable first:")
        print("export OPENAI_API_KEY='your-api-key-here'")
        exit(1)
    
    print("🧪 Starting comprehensive test of multiple sites + built-in LLM system...")
    asyncio.run(main())
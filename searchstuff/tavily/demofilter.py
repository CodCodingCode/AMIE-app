import os
import json
import asyncio
import logging
from datetime import datetime
from typing import Dict, List
from tavily import TavilyClient
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode, LLMConfig
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from pydantic import BaseModel, Field

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FamilyHistoryImpact(BaseModel):
    inheritance_pattern: str = Field(description="How the disease is inherited")
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

async def test_simple_extraction():
    """Simple test with one website to verify our parsing fix"""
    
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        print("❌ Please set OPENAI_API_KEY environment variable")
        return
    
    # Test with just Mayo Clinic
    test_url = "https://www.mayoclinic.org/diseases-conditions/diabetes/symptoms-causes/syc-20371444"
    disease = "diabetes"
    
    print(f"🧪 SIMPLE TEST: Extracting from {test_url}")
    
    browser_config = BrowserConfig(
        headless=True,
        browser_type="chromium",
        java_script_enabled=True,
        verbose=False
    )
    
    extraction_strategy = LLMExtractionStrategy(
        llm_config=LLMConfig(
            provider="openai/gpt-4o-mini",
            api_token=openai_api_key
        ),
        schema=MedicalInformation.model_json_schema(),
        extraction_type="schema",
        instruction=f"Extract comprehensive medical information about {disease}. Focus on symptoms, causes, treatments, diagnosis, risk factors, prevention, prognosis, and genetic factors.",
        verbose=False
    )
    
    crawler_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        extraction_strategy=extraction_strategy,
        verbose=False
    )
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        print("🕷️ Crawling website...")
        
        result = await crawler.arun(url=test_url, config=crawler_config)
        
        if result.success and result.extracted_content:
            print(f"✅ Crawl successful, content length: {len(result.extracted_content)}")
            
            try:
                # THE CORRECTED PARSING LOGIC
                if isinstance(result.extracted_content, str):
                    json_data = json.loads(result.extracted_content)
                    
                    if isinstance(json_data, list):
                        # Find the first non-error object with medical data
                        extracted_data = None
                        print(f"🔍 Found {len(json_data)} objects in extraction results")
                        
                        for i, item in enumerate(json_data):
                            if isinstance(item, dict):
                                if item.get('error') == True:
                                    print(f"  Object {i}: ❌ Error - {item.get('content', 'Unknown error')}")
                                elif 'disease_name' in item:
                                    print(f"  Object {i}: ✅ Medical data found")
                                    extracted_data = item
                                    break
                                else:
                                    print(f"  Object {i}: ⚠️ Unknown structure")
                        
                        if extracted_data is None:
                            print("❌ No valid medical data found")
                            return
                            
                    elif isinstance(json_data, dict):
                        extracted_data = json_data
                    else:
                        print(f"❌ Unexpected JSON structure: {type(json_data)}")
                        return
                else:
                    print(f"❌ Unexpected content type: {type(result.extracted_content)}")
                    return
                
                # SUCCESS! Show extracted data
                print(f"\n🎉 SUCCESS! Extracted medical data:")
                print(f"  Disease: {extracted_data.get('disease_name', 'N/A')}")
                print(f"  Symptoms: {len(extracted_data.get('symptoms', []))} found")
                print(f"  Causes: {len(extracted_data.get('causes', []))} found")
                print(f"  Treatments: {len(extracted_data.get('treatment_options', []))} found")
                print(f"  Risk factors: {len(extracted_data.get('risk_factors', []))} found")
                print(f"  Diagnosis methods: {len(extracted_data.get('diagnosis_methods', []))} found")
                
                if extracted_data.get('symptoms'):
                    print(f"\n📋 Sample symptoms:")
                    for i, symptom in enumerate(extracted_data['symptoms'][:5]):
                        print(f"    {i+1}. {symptom}")
                
                print(f"\n✅ PARSING FIX WORKS! Ready to update main system.")
                return True
                
            except Exception as e:
                print(f"❌ Parsing error: {e}")
                print(f"Raw content preview: {str(result.extracted_content)[:300]}...")
                return False
        else:
            print(f"❌ Crawl failed: {result.error_message if hasattr(result, 'error_message') else 'Unknown error'}")
            return False

async def main():
    print("🧪 TESTING CORRECTED PARSING LOGIC")
    print("="*50)
    
    success = await test_simple_extraction()
    
    if success:
        print("\n🚀 READY TO UPDATE MAIN SYSTEM!")
        print("The parsing fix works - we can now update both test and main files.")
    else:
        print("\n❌ Still need to debug the parsing logic.")

if __name__ == "__main__":
    asyncio.run(main())
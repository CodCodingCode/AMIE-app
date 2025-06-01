import os
import json
import asyncio
import logging
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode, LLMConfig
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from pydantic import BaseModel, Field
from typing import List

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define the medical information schema
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

async def debug_single_extraction():
    """Debug what Crawl4AI actually returns"""
    
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        print("❌ Please set OPENAI_API_KEY environment variable")
        return
    
    # Test with a simple medical website
    test_url = "https://www.mayoclinic.org/diseases-conditions/diabetes/symptoms-causes/syc-20371444"
    disease = "diabetes"
    
    print(f"🔍 Debug: Testing extraction from {test_url}")
    
    # Set up Crawl4AI configuration
    browser_config = BrowserConfig(
        headless=True,
        browser_type="chromium",
        java_script_enabled=True,
        verbose=True
    )
    
    extraction_strategy = LLMExtractionStrategy(
        llm_config=LLMConfig(
            provider="openai/gpt-4o-mini",
            api_token=openai_api_key
        ),
        schema=MedicalInformation.model_json_schema(),
        extraction_type="schema",
        instruction=f"""Extract comprehensive medical information about {disease} from the website content. 
        
        Focus on:
        1. All symptoms and clinical signs
        2. Underlying causes and etiology  
        3. Available treatment options
        4. Diagnostic methods and tests used
        5. Known risk factors
        6. Prevention strategies
        7. Prognosis and outcomes
        8. Genetic and hereditary aspects
        9. Family history implications
        10. Screening recommendations for relatives

        Return a complete JSON object with all fields filled.""",
        verbose=True
    )
    
    crawler_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        word_count_threshold=100,
        extraction_strategy=extraction_strategy,
        verbose=True
    )
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        print("🕷️ Starting crawl...")
        
        result = await crawler.arun(
            url=test_url,
            config=crawler_config
        )
        
        print(f"\n📊 CRAWL RESULTS DEBUG:")
        print(f"✅ Success: {result.success}")
        print(f"📄 Content length: {len(result.markdown)} chars")
        print(f"🧠 Has extracted_content: {hasattr(result, 'extracted_content')}")
        
        if hasattr(result, 'extracted_content'):
            print(f"📦 extracted_content type: {type(result.extracted_content)}")
            print(f"📦 extracted_content length: {len(result.extracted_content) if result.extracted_content else 0}")
            
            if result.extracted_content:
                print(f"\n🔍 RAW EXTRACTED CONTENT:")
                print(f"Type: {type(result.extracted_content)}")
                
                if isinstance(result.extracted_content, list):
                    print(f"List length: {len(result.extracted_content)}")
                    for i, item in enumerate(result.extracted_content):
                        print(f"  Item {i}: {type(item)}")
                        if isinstance(item, str):
                            print(f"    Content preview: {item[:200]}...")
                        elif isinstance(item, dict):
                            print(f"    Dict keys: {list(item.keys())}")
                        else:
                            print(f"    Content: {item}")
                
                elif isinstance(result.extracted_content, str):
                    print(f"String content preview: {result.extracted_content[:300]}...")
                
                elif isinstance(result.extracted_content, dict):
                    print(f"Dict keys: {list(result.extracted_content.keys())}")
                    if 'symptoms' in result.extracted_content:
                        print(f"Sample symptoms: {result.extracted_content['symptoms'][:3]}")
                
                else:
                    print(f"Unknown type content: {result.extracted_content}")
                
                # Try to parse it properly
                print(f"\n🔧 ATTEMPTING TO PARSE:")
                try:
                    if isinstance(result.extracted_content, str):
                        # Parse the JSON string
                        json_data = json.loads(result.extracted_content)
                        print(f"Parsed JSON type: {type(json_data)}")
                        
                        if isinstance(json_data, list) and len(json_data) > 0:
                            print(f"JSON array contains {len(json_data)} items")
                            
                            # Find the first non-error object
                            parsed_data = None
                            for i, item in enumerate(json_data):
                                print(f"  Item {i}: {type(item)}")
                                if isinstance(item, dict):
                                    if item.get('error') == True:
                                        print(f"    ❌ Error object: {item.get('content', 'Unknown error')}")
                                    elif 'disease_name' in item:
                                        print(f"    ✅ Found medical data object")
                                        parsed_data = item
                                        break
                                    else:
                                        print(f"    ⚠️ Unknown object keys: {list(item.keys())}")
                            
                            if parsed_data is None:
                                print(f"❌ No valid medical data found in {len(json_data)} objects")
                                return
                                
                        elif isinstance(json_data, dict):
                            # It's already a dict
                            parsed_data = json_data
                        else:
                            print(f"❌ Unexpected JSON structure: {type(json_data)}")
                            return
                    elif isinstance(result.extracted_content, list) and len(result.extracted_content) > 0:
                        first_item = result.extracted_content[0]
                        print(f"First item type: {type(first_item)}")
                        
                        if isinstance(first_item, dict):
                            parsed_data = first_item
                        elif isinstance(first_item, str):
                            parsed_data = json.loads(first_item)
                        else:
                            print(f"❌ Unknown first item type: {type(first_item)}")
                            return
                    elif isinstance(result.extracted_content, dict):
                        parsed_data = result.extracted_content
                    else:
                        print(f"❌ Cannot parse type: {type(result.extracted_content)}")
                        return
                    
                    print(f"\n✅ SUCCESSFULLY PARSED DATA:")
                    print(f"  Disease: {parsed_data.get('disease_name', 'N/A')}")
                    print(f"  Symptoms: {len(parsed_data.get('symptoms', []))} found")
                    print(f"  Causes: {len(parsed_data.get('causes', []))} found")
                    print(f"  Treatments: {len(parsed_data.get('treatment_options', []))} found")
                    print(f"  Risk factors: {len(parsed_data.get('risk_factors', []))} found")
                    print(f"  Diagnosis methods: {len(parsed_data.get('diagnosis_methods', []))} found")
                    
                    if parsed_data.get('symptoms'):
                        print(f"\n📝 Sample symptoms:")
                        for i, symptom in enumerate(parsed_data['symptoms'][:5]):
                            print(f"    {i+1}. {symptom}")
                    
                    if parsed_data.get('treatment_options'):
                        print(f"\n💊 Sample treatments:")
                        for i, treatment in enumerate(parsed_data['treatment_options'][:3]):
                            print(f"    {i+1}. {treatment}")
                    
                    print(f"\n🎯 CORRECT PARSING METHOD:")
                    print("✅ Parse JSON: json.loads(result.extracted_content)")
                    print("✅ Find non-error object: filter out objects with 'error': true")
                    print("✅ Use object with 'disease_name' key")
                        
                except json.JSONDecodeError as e:
                    print(f"❌ JSON parsing failed: {e}")
                    print(f"Raw content that failed: {result.extracted_content[:500]}...")
                except Exception as e:
                    print(f"❌ Parsing error: {e}")
                    import traceback
                    traceback.print_exc()
            
            else:
                print("❌ extracted_content is empty/None")
        else:
            print("❌ No extracted_content attribute found")
        
        if hasattr(result, 'error_message') and result.error_message:
            print(f"❌ Error message: {result.error_message}")

async def main():
    """Run the debug"""
    await debug_single_extraction()

if __name__ == "__main__":
    asyncio.run(main())
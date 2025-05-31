import os
import json
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Any
from tavily import TavilyClient
from openai import OpenAI
import logging
import time
import asyncio

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestMedicalInfoSystem:
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
        
        # Test results
        self.test_results = []
    
    def _get_tavily_client(self, worker_id: int = 0) -> TavilyClient:
        """Get a Tavily client with key rotation based on worker ID"""
        key_index = worker_id % len(self.tavily_keys)
        return TavilyClient(api_key=self.tavily_keys[key_index])
    
    def _get_openai_client(self) -> OpenAI:
        """Get an OpenAI client (thread-safe)"""
        return OpenAI(api_key=self.openai_api_key)
    
    def test_crawl4ai_import(self):
        """Test if Crawl4AI can be imported and which version/syntax works"""
        logger.info("Testing Crawl4AI imports...")
        
        # Test different import patterns
        import_tests = [
            ("AsyncWebCrawler (v0.6.x)", "from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig"),
            ("WebCrawler (older version)", "from crawl4ai import WebCrawler"),
            ("Basic crawl4ai", "import crawl4ai")
        ]
        
        working_imports = []
        
        for test_name, import_code in import_tests:
            try:
                exec(import_code)
                working_imports.append(test_name)
                logger.info(f"✓ {test_name}: {import_code}")
            except ImportError as e:
                logger.warning(f"✗ {test_name}: {e}")
            except Exception as e:
                logger.error(f"✗ {test_name}: Unexpected error: {e}")
        
        if working_imports:
            logger.info(f"Working imports: {', '.join(working_imports)}")
            return working_imports[0]  # Return the first working import
        else:
            logger.error("No Crawl4AI imports work! Please install crawl4ai: pip install crawl4ai")
            return None
    
    async def test_basic_crawl_v06(self, url: str = "https://en.wikipedia.org/wiki/Diabetes"):
        """Test basic crawling with v0.6.x syntax"""
        try:
            from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
            
            logger.info(f"Testing v0.6.x crawling with URL: {url}")
            
            browser_config = BrowserConfig(
                headless=True,
                browser_type="chromium",
                verbose=False
            )
            
            crawler_config = CrawlerRunConfig(
                cache_mode=CacheMode.BYPASS,
                word_count_threshold=50,
                verbose=False
            )
            
            async with AsyncWebCrawler(config=browser_config) as crawler:
                result = await crawler.arun(url=url, config=crawler_config)
                
                if result.success:
                    content_length = len(result.markdown)
                    logger.info(f"✓ Successfully crawled {content_length} characters")
                    logger.info(f"Content preview: {result.markdown[:200]}...")
                    return result.markdown
                else:
                    logger.error(f"✗ Crawling failed: {result.error_message}")
                    return None
                    
        except Exception as e:
            logger.error(f"✗ v0.6.x crawling failed: {e}")
            return None
    
    def test_basic_crawl_older(self, url: str = "https://en.wikipedia.org/wiki/Diabetes"):
        """Test basic crawling with older WebCrawler syntax"""
        try:
            from crawl4ai import WebCrawler
            
            logger.info(f"Testing older WebCrawler with URL: {url}")
            
            crawler = WebCrawler(headless=True)
            crawler.warmup()
            
            result = crawler.run(url=url)
            
            if result.success:
                content_length = len(result.markdown)
                logger.info(f"✓ Successfully crawled {content_length} characters")
                logger.info(f"Content preview: {result.markdown[:200]}...")
                return result.markdown
            else:
                logger.error(f"✗ Crawling failed: {result.error_message}")
                return None
                
        except Exception as e:
            logger.error(f"✗ Older WebCrawler failed: {e}")
            return None
    
    async def test_search_and_simple_crawl(self, disease: str = "diabetes"):
        """Test the basic workflow: search + crawl without complex extraction"""
        logger.info(f"Testing search and crawl workflow for: {disease}")
        
        # Test Tavily search first
        try:
            tavily_client = self._get_tavily_client()
            search_results = tavily_client.search(
                query=f"Medical information {disease} symptoms causes treatment",
                search_depth="basic",
                max_results=3
            )
            
            urls = [result.get('url', '') for result in search_results.get("results", [])]
            logger.info(f"✓ Found {len(urls)} URLs from Tavily search")
            for i, url in enumerate(urls):
                logger.info(f"  {i+1}. {url}")
                
        except Exception as e:
            logger.error(f"✗ Tavily search failed: {e}")
            return None
        
        # Test crawling the first URL
        if urls:
            test_url = urls[0]
            logger.info(f"Testing crawl of: {test_url}")
            
            # Try v0.6.x first
            content = await self.test_basic_crawl_v06(test_url)
            
            # If that fails, try older version
            if content is None:
                content = self.test_basic_crawl_older(test_url)
            
            if content:
                # Test basic GPT processing
                return await self.test_gpt_extraction(disease, content, test_url)
        
        return None
    
    async def test_gpt_extraction(self, disease: str, content: str, url: str):
        """Test GPT extraction of medical information"""
        try:
            openai_client = self._get_openai_client()
            
            # Truncate content for testing
            if len(content) > 8000:
                content = content[:8000] + "..."
            
            prompt = f"""Analyze the following website content about {disease} and extract medical information. Return a valid JSON object with this structure:

{{
    "disease_name": "{disease}",
    "symptoms": ["symptom1", "symptom2"],
    "causes": ["cause1", "cause2"],
    "treatment_options": ["treatment1", "treatment2"],
    "diagnosis_methods": ["method1", "method2"],
    "risk_factors": ["factor1", "factor2"],
    "prevention": ["prevention1", "prevention2"],
    "prognosis": "brief prognosis description"
}}

Website content from {url}:
{content}

Extract medical information and return only the JSON object."""
            
            response = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=1500
            )
            
            content_response = response.choices[0].message.content.strip()
            
            # Try to parse JSON
            start_idx = content_response.find('{')
            end_idx = content_response.rfind('}') + 1
            
            if start_idx != -1 and end_idx > start_idx:
                json_str = content_response[start_idx:end_idx]
                structured_info = json.loads(json_str)
                
                logger.info("✓ Successfully extracted medical information:")
                logger.info(f"  Disease: {structured_info.get('disease_name', 'N/A')}")
                logger.info(f"  Symptoms: {len(structured_info.get('symptoms', []))} found")
                logger.info(f"  Causes: {len(structured_info.get('causes', []))} found")
                logger.info(f"  Treatments: {len(structured_info.get('treatment_options', []))} found")
                
                return structured_info
            else:
                logger.error("✗ Could not find valid JSON in GPT response")
                logger.error(f"Response: {content_response[:300]}...")
                return None
                
        except json.JSONDecodeError as e:
            logger.error(f"✗ JSON parsing failed: {e}")
            return None
        except Exception as e:
            logger.error(f"✗ GPT extraction failed: {e}")
            return None
    
    async def run_full_test(self, test_disease: str = "diabetes"):
        """Run the complete test suite"""
        logger.info("="*60)
        logger.info("STARTING MEDICAL INFO SYSTEM TEST")
        logger.info("="*60)
        
        # Test 1: Import testing
        logger.info("\n1. Testing Crawl4AI imports...")
        working_import = self.test_crawl4ai_import()
        
        if not working_import:
            logger.error("CRITICAL: No working Crawl4AI imports found!")
            return False
        
        # Test 2: API keys
        logger.info("\n2. Testing API keys...")
        if not self.openai_api_key:
            logger.error("CRITICAL: OpenAI API key not found!")
            return False
        else:
            logger.info("✓ OpenAI API key found")
        
        # Test Tavily
        try:
            tavily_client = self._get_tavily_client()
            test_search = tavily_client.search(query="test", max_results=1)
            logger.info("✓ Tavily API key working")
        except Exception as e:
            logger.error(f"✗ Tavily API test failed: {e}")
            return False
        
        # Test 3: Full workflow
        logger.info(f"\n3. Testing full workflow with '{test_disease}'...")
        result = await self.test_search_and_simple_crawl(test_disease)
        
        if result:
            logger.info("\n✓ FULL TEST PASSED!")
            logger.info("The system should work with your complete disease dataset.")
            
            # Save test result
            test_output = {
                'test_disease': test_disease,
                'test_timestamp': datetime.now().isoformat(),
                'working_import': working_import,
                'extracted_data': result
            }
            
            with open('test_results.json', 'w') as f:
                json.dump(test_output, f, indent=2)
            
            logger.info("Test results saved to 'test_results.json'")
            return True
        else:
            logger.error("\n✗ FULL TEST FAILED!")
            logger.error("Please check the errors above and fix issues before running the full system.")
            return False


async def main():
    """Run the test"""
    try:
        tester = TestMedicalInfoSystem()
        success = await tester.run_full_test("diabetes")
        
        if success:
            print("\n🎉 ALL TESTS PASSED! Your system is ready to process diseases.")
            print("You can now run the full medical_info_system.py script.")
        else:
            print("\n❌ TESTS FAILED! Please fix the issues above.")
            
    except Exception as e:
        logger.error(f"Test runner failed: {e}")
        print(f"\n❌ Test runner error: {e}")


if __name__ == "__main__":
    # Make sure we have the required environment variable
    if not os.getenv("OPENAI_API_KEY"):
        print("Please set your OPENAI_API_KEY environment variable first:")
        print("export OPENAI_API_KEY='your-api-key-here'")
        exit(1)
    
    asyncio.run(main())
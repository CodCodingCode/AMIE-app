import asyncio
from tavily import TavilyClient
from crawl4ai import AsyncWebCrawler
from openai import OpenAI
import pandas as pd
import os
import json
import time
from typing import List, Dict

# Initialize clients
tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Disease Categories (simplified)
DISEASE_CATEGORIES = [
    "infectious diseases",
    "cancer diseases", 
    "heart diseases",
    "lung diseases",
    "brain diseases",
    "eye diseases",
    "skin diseases",
    "bone diseases",
    "kidney diseases",
    "liver diseases",
    "digestive diseases",
    "mental health disorders",
    "blood disorders",
    "immune system diseases",
    "metabolic diseases",
    "genetic diseases",
    "autoimmune diseases",
    "respiratory diseases",
    "neurological diseases",
    "endocrine diseases"
]

async def search_diseases_for_category(category: str) -> List[Dict]:
    """
    Search for diseases in a specific category using Tavily and extract with OpenAI
    """
    print(f"\nSearching for diseases in category: {category}")
    
    # Simple search queries for the category
    search_queries = [
        f"common {category} list",
        f"most frequent {category}",
        f"{category} examples medical conditions"
    ]
    
    all_urls = set()
    
    # Get URLs from search queries
    for query in search_queries:
        try:
            print(f"  Searching: {query}")
            search_result = tavily_client.search(
                query=query,
                search_depth="basic",
                max_results=3
            )
            
            for result in search_result.get('results', []):
                url = result.get('url')
                if url:
                    all_urls.add(url)
            
            time.sleep(0.5)  # Reduced delay for parallel processing
            
        except Exception as e:
            print(f"    Error searching for {query}: {e}")
    
    print(f"  Found {len(all_urls)} URLs to crawl")
    
    # Crawl URLs and collect content
    all_content = []
    async with AsyncWebCrawler(verbose=False) as crawler:
        for url in list(all_urls)[:4]:  # Limit to 4 URLs
            try:
                print(f"  Crawling: {url}")
                result = await crawler.arun(url=url)
                
                if result.success and result.markdown:
                    all_content.append({
                        'url': url,
                        'content': result.markdown[:3000]  # Limit content length
                    })
                    print(f"    Got {len(result.markdown)} chars of content")
                        
            except Exception as e:
                print(f"    Error crawling {url}: {e}")
    
    print(f"  Crawled {len(all_content)} pages successfully")
    
    # Extract diseases using OpenAI
    if all_content:
        diseases = await extract_diseases_with_openai(category, all_content)
        return diseases
    else:
        print(f"  No content found for {category}")
        return []

async def extract_diseases_with_openai(category: str, content_list: List[Dict]) -> List[Dict]:
    """
    Use OpenAI to extract diseases from crawled content
    """
    print(f"  Extracting diseases using OpenAI...")
    
    # Combine content from all sources
    combined_content = "\n\n".join([
        f"Source: {item['url']}\n{item['content']}" 
        for item in content_list
    ])
    
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "user",
                "content": f"""Extract ALL specific diseases from the category "{category}" based on the following content. Don't limit the number - get as many as you can find.

For each disease, provide the information in this JSON format:
{{
  "name": "specific disease name",
  "description": "brief description", 
  "prevalence_percentage": estimated_percentage_as_number,
  "acute_chronic": "Acute/Chronic/Both"
}}

Return ONLY a JSON array of disease objects. Focus on specific disease names, not broad categories.

Content to analyze:
{combined_content[:6000]}

Example output format:
[
  {{"name": "Influenza", "description": "Viral respiratory infection", "prevalence_percentage": 5.0, "acute_chronic": "Acute"}},
  {{"name": "Tuberculosis", "description": "Bacterial lung infection", "prevalence_percentage": 1.5, "acute_chronic": "Chronic"}}
]
"""
            }],
            temperature=0.3,
            max_tokens=1500
        )
        
        response_text = response.choices[0].message.content.strip()
        print(f"    OpenAI response length: {len(response_text)} chars")
        
        # Parse JSON response
        try:
            # Find and extract JSON array
            start_idx = response_text.find('[')
            end_idx = response_text.rfind(']') + 1
            
            if start_idx != -1 and end_idx > start_idx:
                json_text = response_text[start_idx:end_idx]
                diseases = json.loads(json_text)
                
                # Add category to each disease
                for disease in diseases:
                    disease['category'] = category
                
                print(f"    Successfully extracted {len(diseases)} diseases")
                return diseases
            else:
                print(f"    No JSON array found in response")
                return []
                
        except json.JSONDecodeError as e:
            print(f"    JSON parsing error: {e}")
            print(f"    Response text: {response_text[:200]}...")
            return []
            
    except Exception as e:
        print(f"    OpenAI API error: {e}")
        return []

async def search_all_categories(categories: List[str], max_workers: int = 8):
    """
    Search for diseases across all categories using parallel processing
    """
    print(f"Processing {len(categories)} categories with {max_workers} parallel workers...")
    
    # Create semaphore to limit concurrent operations
    semaphore = asyncio.Semaphore(max_workers)
    
    async def process_category_with_semaphore(category: str) -> List[Dict]:
        async with semaphore:
            try:
                print(f"Starting: {category}")
                diseases = await search_diseases_for_category(category)
                print(f"Completed: {category} - Found {len(diseases)} diseases")
                return diseases
            except Exception as e:
                print(f"Error processing {category}: {e}")
                return []
    
    # Create tasks for all categories
    tasks = [process_category_with_semaphore(category) for category in categories]
    
    # Run all tasks concurrently
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Collect all diseases
    all_diseases = []
    for i, result in enumerate(results):
        if isinstance(result, list):
            all_diseases.extend(result)
        else:
            print(f"Error in category {categories[i]}: {result}")
    
    return all_diseases

def save_results(diseases: List[Dict], filename: str = "diseases_by_category.csv"):
    """
    Save the results to a CSV file
    """
    if not diseases:
        print("No diseases found to save!")
        return
    
    df = pd.DataFrame(diseases)
    
    # Clean up the data
    df = df.dropna(subset=['name'])  # Remove entries without names
    df = df.drop_duplicates(subset=['name'], keep='first')  # Remove duplicates
    
    df.to_csv(filename, index=False)
    print(f"\nSaved {len(df)} diseases to {filename}")
    
    # Show summary statistics
    print(f"\nSummary:")
    print(f"Total diseases found: {len(df)}")
    print(f"Categories covered: {df['category'].nunique()}")
    
    if len(df) > 0:
        print(f"Average diseases per category: {len(df) / df['category'].nunique():.1f}")
        
        # Show some examples
        print(f"\nSample diseases found:")
        for category in df['category'].unique()[:3]:
            category_diseases = df[df['category'] == category]['name'].head(3).tolist()
            print(f"  {category}: {', '.join(category_diseases)}")

async def main():
    """
    Main function to run the disease search
    """
    print("Starting disease search across categories...")
    print(f"Will extract ALL diseases found in each category")
    
    # Search ALL categories
    categories_to_search = DISEASE_CATEGORIES
    
    # If you want to test with fewer categories first, use:
    # categories_to_search = DISEASE_CATEGORIES[:5]  # First 5 categories
    
    print(f"Categories to search: {categories_to_search}")
    
    diseases = await search_all_categories(categories_to_search, max_workers=8)
    
    save_results(diseases, "diseases_by_category.csv")
    
    print(f"\nSearch completed! Check 'diseases_by_category.csv' for results.")

if __name__ == "__main__":
    # Make sure you have the required API keys set as environment variables:
    # export TAVILY_API_KEY="your_tavily_key"  
    # export OPENAI_API_KEY="your_openai_key"
    
    asyncio.run(main())
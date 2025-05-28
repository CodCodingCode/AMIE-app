import asyncio
import json
from urllib.parse import urljoin

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BrowserConfig, CacheMode
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy


async def single_url_example():
    browser_conf = BrowserConfig(headless=True, verbose=False)
    # Example: Extract specific data using CSS selectors
    run_conf = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        extraction_strategy=JsonCssExtractionStrategy(
            schema={
                "baseSelector": "main",  # Add baseSelector to point to the main content area
                "fields": [  # Define fields at the top level
                    {
                        "name": "title",
                        "selector": "h1",  # Extract text content of the first H1
                        "type": "text",
                    },
                    {
                        "name": "links",  # Extract all links within the main content area
                        "selector": "main a",
                        "type": "list",
                        "fields": {
                            "text": "a",  # Link text
                            "href": {
                                "selector": "a",
                                "type": "attribute",
                                "attribute": "href",
                            },  # Link URL
                        },
                    },
                ],
            }
        ),
        # Remove the output_formats argument if it's not supported
        # output_formats=["markdown", "extracted_content"],  # Request both outputs
    )

    async with AsyncWebCrawler(config=browser_conf) as crawler:
        target_url = "https://docs.crawl4ai.com/"
        print(f"Crawling single URL: {target_url}")
        result = await crawler.arun(url=target_url, config=run_conf)

        if result and result.success:
            print("Single URL Crawl Successful.")
            # Debugging: Print the entire markdown result to see available attributes
            print("Markdown Result:", result.markdown)

            # Check if word_count exists before accessing it
            if hasattr(result.markdown, "word_count"):
                print(f"Fit Markdown Word Count: {result.markdown.word_count}")
            else:
                print("Word count attribute not found in markdown result.")

            if result.extracted_content:
                print("Extracted Content:")
                # Assuming JSON output from the strategy
                print(json.dumps(json.loads(result.extracted_content), indent=2))
            else:
                print("No content extracted based on schema.")
        else:
            print(f"Crawl Failed for {target_url}. Error: {result.error_message}")


if __name__ == "__main__":
    asyncio.run(single_url_example())

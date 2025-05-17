import requests
from bs4 import BeautifulSoup
import string
import time
import json

base_url = "https://www.medicinenet.com/diseases_and_conditions/"
all_results = []


# Define full article scraping function
def scrape_condition_page(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # Get title
        title_tag = soup.find("h2")
        title = title_tag.get_text(strip=True) if title_tag else "No title found"

        # ✅ Get all paragraph text from anywhere on the page
        paragraphs = soup.find_all("p")
        full_text = "\n".join(
            p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)
        )

        return {"url": url, "title": title, "text": full_text}

    except Exception as e:
        print(f"❌ Failed to scrape {url}: {e}")
        return {"url": url, "title": None, "text": None}


# Loop through A to Z
for letter in string.ascii_lowercase:
    url = f"{base_url}alpha_{letter}.htm"
    print(f"\n📄 Scraping list: {url}")
    response = requests.get(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        },
        timeout=10,
    )
    response.raise_for_status()

    # Parse HTML
    soup = BeautifulSoup(response.text, "html.parser")

    # Select all disease links
    disease_links = soup.select("a")

    # Extract text and href
    for a in disease_links:
        link = a.get("href")

        # ✅ Skip non-article links
        if not link or not link.endswith("/article.htm"):

            continue

        # ✅ Add domain prefix if missing
        if link.startswith("/"):
            link = f"https://www.medicinenet.com{link}"

        # Scrape article content from each condition link
        condition_data = scrape_condition_page(link)

        # Save combined result
        all_results.append(
            {
                "article_title": condition_data["title"],
                "article_text": condition_data["text"],
            }
        )

        time.sleep(1)  # Be polite

# Save to file
with open("medicinenet.json", "w") as f:
    json.dump(all_results, f, indent=2)

print(
    f"\n✅ Scraping complete. {len(all_results)} conditions saved to familydoctor_conditions.json."
)

import requests
from bs4 import BeautifulSoup
import string
import time
import json

base_url = "https://familydoctor.org/diseases-and-conditions/"
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
for letter in string.ascii_uppercase:
    for page in range(1, 6):
        try:
            url = f"{base_url}?alpha={letter}&pagenum={page}"
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
            disease_links = soup.select("a.link-to-post")

            # Extract text and href
            for a in disease_links:
                title = a.get_text(strip=True)
                link = a["href"]
                print(f"🔗 {title} → {link}")

                # Scrape article content from each condition link
                condition_data = scrape_condition_page(link)

                # Save combined result
                all_results.append(
                    {
                        "list_title": title,
                        "article_title": condition_data["title"],
                        "article_text": condition_data["text"],
                    }
                )

                time.sleep(1)  # Be polite

        except Exception as e:
            print(f"⚠️ Error on {url}: {e}")
            continue

# Save to file
with open("familydoctor_conditions.json", "w") as f:
    json.dump(all_results, f, indent=2)

print(
    f"\n✅ Scraping complete. {len(all_results)} conditions saved to familydoctor_conditions.json."
)

import requests

def search_medlineplus_diagnosis(code: str, code_system: str = "ICD-9-CM", language: str = "en", output_format: str = "json"):
    # Code system mappings
    code_systems = {
        "ICD-9-CM": "2.16.840.1.113883.6.103",
        "ICD-10-CM": "2.16.840.1.113883.6.90",
        "SNOMED-CT": "2.16.840.1.113883.6.96",
    }

    base_url = "https://connect.medlineplus.gov/service"

    params = {
        "mainSearchCriteria.v.cs": code_systems.get(code_system),
        "mainSearchCriteria.v.c": code,
        "informationRecipient.languageCode.c": language,
        "knowledgeResponseType": f"application/{output_format}",
    }

    response = requests.get(base_url, params=params)

    if response.status_code == 200:
        data = response.json()
        entries = data.get("feed", {}).get("entry", [])

        results = []
        for entry in entries:
            link_data = entry.get("link", [])
            # Get the first link with rel="alternate", if any
            href = None
            for link in link_data:
                if link.get("rel") == "alternate":
                    href = link.get("href")
                    break

            results.append({
                "title": entry.get("title", ""),
                "link": href,
                "summary": entry.get("summary", {}).get("$", ""),
            })
        return results
    else:
        raise Exception(f"Request failed with status code {response.status_code}")

if __name__ == "__main__":
    result = search_medlineplus_diagnosis("250.33", code_system="ICD-9-CM", language="en")
    for item in result:
        print(item)
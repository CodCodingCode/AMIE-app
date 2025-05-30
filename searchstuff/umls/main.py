import requests

API_KEY = "8da8b4db-38db-486c-9078-2587d19b9f6a"
BASE_URL = "https://uts-ws.nlm.nih.gov/rest"
VERSION = "current"

def get_concept_info(cui: str):
    """Get basic information about a concept from its CUI."""
    url = f"{BASE_URL}/content/{VERSION}/CUI/{cui}"
    params = {"apiKey": API_KEY}
    response = requests.get(url, params=params)
    return response.json()

cui = "C0000814" 
concept_info = get_concept_info(cui)

print("CUI:", cui)
print("Name:", concept_info["result"]["name"])
print("Semantic Types:", [stype["name"] for stype in concept_info["result"]["semanticTypes"]])
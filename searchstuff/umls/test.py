import requests
import json

API_KEY = "8da8b4db-38db-486c-9078-2587d19b9f6a"

def test_all_endpoints(cui="C0009443"):  # Common Cold CUI
    """Test all possible endpoints to find the detailed content"""
    
    results = {}
    
    # 1. Basic concept info
    print("=== BASIC CONCEPT INFO ===")
    url = f"https://uts-ws.nlm.nih.gov/rest/content/current/CUI/{cui}"
    response = requests.get(url, params={"apiKey": API_KEY})
    if response.status_code == 200:
        data = response.json()
        results['concept_info'] = data
        print(f"Name: {data.get('result', {}).get('name', '')}")
        print(f"Keys available: {list(data.get('result', {}).keys())}")
    
    # 2. Definitions
    print("\n=== DEFINITIONS ===")
    url = f"https://uts-ws.nlm.nih.gov/rest/content/current/CUI/{cui}/definitions"
    response = requests.get(url, params={"apiKey": API_KEY})
    if response.status_code == 200:
        data = response.json()
        results['definitions'] = data
        for i, defn in enumerate(data.get('result', [])[:3]):  # First 3
            print(f"Definition {i+1}: {defn.get('value', '')[:200]}...")
            print(f"Source: {defn.get('rootSource', '')}")
    
    # 3. Atoms (what you were getting)
    print("\n=== ATOMS (first 5) ===")
    url = f"https://uts-ws.nlm.nih.gov/rest/content/current/CUI/{cui}/atoms"
    response = requests.get(url, params={"apiKey": API_KEY, "pageSize": 20})
    if response.status_code == 200:
        data = response.json()
        results['atoms'] = data
        for i, atom in enumerate(data.get('result', [])[:5]):
            print(f"Atom {i+1}: {atom.get('name', '')}")
            print(f"  Source: {atom.get('rootSource', '')}, Type: {atom.get('termType', '')}")
    
    # 4. Relations
    print("\n=== RELATIONS (first 3) ===")
    url = f"https://uts-ws.nlm.nih.gov/rest/content/current/CUI/{cui}/relations"
    response = requests.get(url, params={"apiKey": API_KEY})
    if response.status_code == 200:
        data = response.json()
        results['relations'] = data
        for i, rel in enumerate(data.get('result', [])[:3]):
            print(f"Relation {i+1}: {rel.get('relatedIdName', '')} ({rel.get('relationLabel', '')})")
    
    # Save full results to see everything
    with open('common_cold_test.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nFull results saved to common_cold_test.json")
    return results

# Test it
test_all_endpoints()
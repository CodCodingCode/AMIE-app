import requests

def get_health_topics(query, max_results=5):
    url = "https://wsearch.nlm.nih.gov/ws/query"
    params = {
        "db": "healthTopics",
        "term": query,
        "retmax": max_results,
        "rettype": "json"
    }
    response = requests.get(url, params=params)
    data = response.json()
    return data

results = get_health_topics("asthma")
print(results)

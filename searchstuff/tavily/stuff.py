import os
from tavily import TavilyClient
from openai import OpenAI

# Set your API keys
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize Tavily client
tavily = TavilyClient(api_key=TAVILY_API_KEY)

# Initialize OpenAI client (v1+ syntax)
client = OpenAI(api_key=OPENAI_API_KEY)

def get_medical_info(disease: str):
    # Step 1: Search with Tavily
    query = f"Symptoms, treatment, causes, family history, and other medical info about {disease}"
    search_results = tavily.search(query=query, search_depth="advanced", include_answer=False)

    # Step 2: Extract snippets
    sources = "\n\n".join([
        f"{result['title']}\n{result['content']}"
        for result in search_results["results"][:5]
    ])

    # Step 3: Summarize using OpenAI
    prompt = f"""
You are a medical assistant. Summarize the following information about the disease: {disease}.
Include:
- Symptoms
- Treatment options
- Causes
- Any relevant facts

Sources:
{sources}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,
    )

    return response.choices[0].message.content.strip()

# Example usage
if __name__ == "__main__":
    disease_name = input("Enter a disease: ")
    info = get_medical_info(disease_name)
    print("\n--- Medical Information ---\n")
    print(info)

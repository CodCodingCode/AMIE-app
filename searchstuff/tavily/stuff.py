import os
from medical_info_system import MedicalInfoSystem

def get_medical_info(disease: str):
    """
    Legacy function - now uses the new MedicalInfoSystem
    
    Args:
        disease: Name of the disease to research
        
    Returns:
        Formatted medical information string
    """
    try:
        system = MedicalInfoSystem()
        result = system.search_medical_info(disease)
        
        if 'error' in result:
            return f"Error retrieving information for {disease}: {result['error']}"
        
        # Format the result similar to the original output
        formatted_info = f"""
Medical Information for {result.get('disease_name', disease)}:

SUMMARY:
{result.get('summary', 'No summary available')}

SYMPTOMS:
{', '.join(result.get('symptoms', ['No symptoms information available']))}

CAUSES:
{', '.join(result.get('causes', ['No causes information available']))}

TREATMENT OPTIONS:
{', '.join(result.get('treatment_options', ['No treatment information available']))}

DIAGNOSIS METHODS:
{', '.join(result.get('diagnosis_methods', ['No diagnosis information available']))}

RISK FACTORS:
{', '.join(result.get('risk_factors', ['No risk factors information available']))}

PREVENTION:
{', '.join(result.get('prevention', ['No prevention information available']))}

PROGNOSIS:
{result.get('prognosis', 'No prognosis information available')}

Sources used: {result.get('sources_count', 0)}
Search confidence: {result.get('search_confidence', 0):.2f}
"""
        
        # Also save to CSV/JSON for future reference
        system.save_to_csv(result)
        system.save_to_json(result)
        
        return formatted_info.strip()
        
    except Exception as e:
        return f"Error: {str(e)}"

# Example usage (maintains backward compatibility)
if __name__ == "__main__":
    print("Enhanced Medical Information System")
    print("=" * 50)
    
    # Check if API keys are set
    if not os.getenv("TAVILY_API_KEY") or not os.getenv("OPENAI_API_KEY"):
        print("Please set TAVILY_API_KEY and OPENAI_API_KEY environment variables")
        print("\nFor the full system, use: python medical_info_system.py")
        exit(1)
    
    # Original functionality
    disease_name = input("Enter a disease: ")
    if disease_name.strip():
        print("\n--- Medical Information ---\n")
        info = get_medical_info(disease_name)
        print(info)
        
        print(f"\n--- Additional Information ---")
        print("This information has been saved to:")
        print("- medical_research_results.csv")
        print("- medical_research_results.json")
        print("\nFor more features, run: python medical_info_system.py")
    else:
        print("No disease name provided.")

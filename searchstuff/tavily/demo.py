#!/usr/bin/env python3
"""
Demo script for the Medical Information System

This script demonstrates different ways to use the medical information system:
1. Single disease query
2. Batch processing from CSV
3. Interactive mode

Make sure to set your API keys:
export TAVILY_API_KEY="your_tavily_api_key"
export OPENAI_API_KEY="your_openai_api_key"
"""

import os
from medical_info_system import MedicalInfoSystem

def demo_single_query():
    """Demo: Single disease query"""
    print("=== Demo: Single Disease Query ===")
    
    system = MedicalInfoSystem()
    
    # Example diseases to try
    diseases = ["diabetes", "hypertension", "asthma", "pneumonia"]
    
    for disease in diseases[:2]:  # Process first 2 for demo
        print(f"\nProcessing: {disease}")
        result = system.process_disease(disease)
        
        if 'error' not in result:
            print(f"✓ Successfully processed {disease}")
            print(f"  - Found {len(result.get('symptoms', []))} symptoms")
            print(f"  - Found {len(result.get('treatment_options', []))} treatment options")
            print(f"  - Sources: {result.get('sources_count', 0)}")
        else:
            print(f"✗ Error processing {disease}: {result['error']}")

def demo_csv_selection():
    """Demo: Select diseases from CSV"""
    print("\n=== Demo: CSV Disease Selection ===")
    
    system = MedicalInfoSystem()
    
    # Get some diseases from CSV
    diseases = system.get_diseases_from_csv(limit=5, filter_terms=['pneumonia', 'syndrome'])
    
    if diseases:
        print(f"Found {len(diseases)} diseases in CSV:")
        for i, disease in enumerate(diseases, 1):
            print(f"  {i}. {disease}")
        
        # Process the first one as demo
        if diseases:
            print(f"\nProcessing first disease: {diseases[0]}")
            result = system.process_disease(diseases[0])
            system.display_result(result)
    else:
        print("No diseases found in CSV")

def demo_batch_processing():
    """Demo: Batch processing (small batch)"""
    print("\n=== Demo: Batch Processing ===")
    
    system = MedicalInfoSystem()
    
    # Get a small batch for demo
    diseases = system.get_diseases_from_csv(limit=3, filter_terms=['syndrome'])
    
    if diseases:
        print(f"Batch processing {len(diseases)} diseases...")
        results = system.batch_process_diseases(diseases, delay=1.0)
        
        print(f"\nBatch processing completed!")
        print(f"Processed {len(results)} diseases")
        
        successful = sum(1 for r in results if 'error' not in r)
        print(f"Successful: {successful}")
        print(f"Errors: {len(results) - successful}")
    else:
        print("No diseases found for batch processing")

def main():
    """Main demo function"""
    print("Medical Information System - Demo")
    print("=" * 50)
    
    # Check if API keys are set
    if not os.getenv("TAVILY_API_KEY") or not os.getenv("OPENAI_API_KEY"):
        print("ERROR: Please set TAVILY_API_KEY and OPENAI_API_KEY environment variables")
        print("\nExample:")
        print("export TAVILY_API_KEY='your_tavily_key'")
        print("export OPENAI_API_KEY='your_openai_key'")
        return
    
    try:
        # Run demos
        demo_single_query()
        demo_csv_selection()
        # demo_batch_processing()  # Uncomment for batch processing demo
        
        print("\n" + "=" * 50)
        print("Demo completed!")
        print("\nFiles created:")
        print("- medical_research_results.csv (structured data)")
        print("- medical_research_results.json (detailed data)")
        print("\nTo run the full interactive system:")
        print("python medical_info_system.py")
        
    except Exception as e:
        print(f"Demo error: {e}")

if __name__ == "__main__":
    main() 
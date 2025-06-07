# main.py
"""
Main entry point for the medical diagnosis simulation system.
"""

import multiprocessing
from process_vignette import process_vignette
from utils import (
    setup_output_directories,
    aggregate_results,
    print_summary_statistics,
    load_vignettes,
)
import os

# Store configuration as module-level constants
API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = "gpt-4.1-nano"


def run_vignette_task(args):
    """Wrapper for multiprocessing pool"""
    idx, vignette_text, disease, api_key, model = args
    
    # Create OpenAI client within the process to avoid pickling issues
    from openai import OpenAI
    client = OpenAI(api_key=api_key)
    
    try:
        return process_vignette(idx, vignette_text, disease, client, model)
    except Exception as e:
        print(f"❌ Error processing vignette {idx} ({disease}): {str(e)}")
        import traceback
        traceback.print_exc()
        # Return None for failed vignettes
        return None


def main():
    """Main execution function"""
    # Check API key
    if not API_KEY:
        raise ValueError("Please set OPENAI_API_KEY environment variable")
    
    # Setup output directories
    setup_output_directories()
    
    # Specify which types to include
    DESIRED_TYPES = ["typical", "severe"]  # Change these as needed
    # Options: "typical", "early", "severe", "mixed"
    
    # Load vignettes
    flattened_vignettes = load_vignettes(
        "patient_roleplay_scripts.json",
        desired_types=DESIRED_TYPES
    )
    
    print(f"📊 Processing {len(flattened_vignettes)} vignettes...")
    
    # Launch multiprocessing pool
    with multiprocessing.Pool(processes=8) as pool:
        results = pool.map(
            run_vignette_task,
            [
                (idx, vignette_text, disease, API_KEY, MODEL)
                for idx, (disease, vignette_text) in enumerate(flattened_vignettes)
            ],
        )
    
    # Filter out any failed results (None values)
    successful_results = [r for r in results if r is not None]
    
    if len(successful_results) < len(results):
        print(f"⚠️ Warning: {len(results) - len(successful_results)} vignettes failed to process")
    
    # Aggregate results
    aggregated = aggregate_results(successful_results)
    
    print("\n✅ All role outputs saved with gold diagnosis guidance and empathetic behavioral adaptations.")
    
    # Print summary statistics
    print_summary_statistics(
        aggregated["behavior_metadata"],
        aggregated["diagnosing_doctor_outputs"],
        aggregated["behavioral_analyses"]
    )


if __name__ == "__main__":
    main()
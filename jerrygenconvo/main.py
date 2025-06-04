# main.py
"""
Main entry point for the medical diagnosis simulation system.
"""

import multiprocessing
from openai import OpenAI
from process_vignette import process_vignette
from utils import (
    setup_output_directories,
    aggregate_results,
    print_summary_statistics,
    load_vignettes,
)


# Initialize OpenAI client
client = OpenAI(api_key="api")
model = "gpt-4.1-nano"


def run_vignette_task(args):
    """Wrapper for multiprocessing pool"""
    idx, vignette_text, disease = args
    return process_vignette(idx, vignette_text, disease, client, model)


def main():
    """Main execution function"""
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
    
    # Launch multiprocessing pool
    with multiprocessing.Pool(processes=12) as pool:
        results = pool.map(
            run_vignette_task,
            [
                (idx, vignette_text, disease)
                for idx, (disease, vignette_text) in enumerate(flattened_vignettes)
            ],
        )
    
    # Aggregate results
    aggregated = aggregate_results(results)
    
    print("\n✅ All role outputs saved with gold diagnosis guidance and empathetic behavioral adaptations.")
    
    # Print summary statistics
    print_summary_statistics(
        aggregated["behavior_metadata"],
        aggregated["diagnosing_doctor_outputs"],
        aggregated["behavioral_analyses"]
    )


if __name__ == "__main__":
    main()
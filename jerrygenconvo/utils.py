# utils.py
"""
Utility functions for the medical diagnosis simulation system.
"""

import os
import shutil
import json


def setup_output_directories():
    """Remove and recreate output directories to start empty"""
    output_dirs = [
        "2summarizer_outputs",
        "2patient_followups",
        "2diagnosing_doctor_outputs",
        "2questioning_doctor_outputs",
        "2treatment_plans",
        "2behavior_metadata",
        "2behavioral_analyses",
        "2accuracy_evaluations",
    ]
    
    for directory in output_dirs:
        if os.path.exists(directory):
            shutil.rmtree(directory)
        os.makedirs(directory, exist_ok=True)
    
    return output_dirs


def save_outputs(idx, outputs_dict):
    """Save all outputs for a given vignette index"""
    for output_type, data in outputs_dict.items():
        filename = f"2{output_type}/{output_type.split('_')[0]}_{idx}.json"
        with open(filename, "w") as f:
            json.dump(data, f, indent=2)


def aggregate_results(results):
    """Aggregate all results from multiprocessing"""
    all_patient_followups = []
    all_summarizer_outputs = []
    all_diagnosing_doctor_outputs = []
    all_questioning_doctor_outputs = []
    all_treatment_plans = []
    all_behavior_metadata = []
    all_behavioral_analyses = []

    for result in results:
        all_patient_followups.extend(result["patient_response"])
        all_summarizer_outputs.extend(result["summarizer_outputs"])
        all_diagnosing_doctor_outputs.extend(result["diagnosing_doctor_outputs"])
        all_questioning_doctor_outputs.extend(result["questioning_doctor_outputs"])
        all_treatment_plans.extend(result["treatment_plans"])
        all_behavior_metadata.append(result["behavior_metadata"])
        all_behavioral_analyses.extend(result["behavioral_analyses"])

    # Save aggregated results
    aggregated = {
        "2patient_followups.json": all_patient_followups,
        "2summarizer_outputs.json": all_summarizer_outputs,
        "2diagnosing_doctor_outputs.json": all_diagnosing_doctor_outputs,
        "2questioning_doctor_outputs.json": all_questioning_doctor_outputs,
        "2treatment_plans.json": all_treatment_plans,
        "2behavior_metadata.json": all_behavior_metadata,
        "2behavioral_analyses.json": all_behavioral_analyses,
    }
    
    for filename, data in aggregated.items():
        with open(filename, "w") as f:
            json.dump(data, f, indent=2)
    
    return {
        "patient_followups": all_patient_followups,
        "summarizer_outputs": all_summarizer_outputs,
        "diagnosing_doctor_outputs": all_diagnosing_doctor_outputs,
        "questioning_doctor_outputs": all_questioning_doctor_outputs,
        "treatment_plans": all_treatment_plans,
        "behavior_metadata": all_behavior_metadata,
        "behavioral_analyses": all_behavioral_analyses,
    }


def print_summary_statistics(all_behavior_metadata, all_diagnosing_doctor_outputs, all_behavioral_analyses):
    """Print summary statistics for the simulation run"""
    
    # Print behavior distribution summary
    behavior_counts = {}
    for metadata in all_behavior_metadata:
        behavior_type = metadata["behavior_type"]
        behavior_counts[behavior_type] = behavior_counts.get(behavior_type, 0) + 1

    print("\n📊 Patient Behavior Distribution:")
    for behavior, count in behavior_counts.items():
        percentage = (count / len(all_behavior_metadata)) * 100
        print(f"  {behavior}: {count} cases ({percentage:.1f}%)")

    # Print diagnostic accuracy summary
    total_cases = len(all_diagnosing_doctor_outputs)
    accurate_diagnoses = sum(
        1
        for output in all_diagnosing_doctor_outputs
        if output.get("accuracy_evaluation", {}).get("gold_diagnosis_found", False)
    )

    print(f"\n🎯 DIAGNOSTIC ACCURACY SUMMARY:")
    print(f"   Total cases processed: {total_cases}")
    print(f"   Gold diagnosis found: {accurate_diagnoses}")
    print(
        f"   Overall accuracy: {(accurate_diagnoses/total_cases)*100:.1f}%"
        if total_cases > 0
        else "   No cases processed"
    )

    # Print accuracy by stage
    stages = {"E": "Early", "M": "Middle", "L": "Late"}
    for stage_letter, stage_name in stages.items():
        stage_cases = [
            output
            for output in all_diagnosing_doctor_outputs
            if output.get("letter") == stage_letter
        ]
        stage_accurate = sum(
            1
            for case in stage_cases
            if case.get("accuracy_evaluation", {}).get("gold_diagnosis_found", False)
        )
        if stage_cases:
            stage_accuracy = (stage_accurate / len(stage_cases)) * 100
            print(
                f"   {stage_name} stage accuracy: {stage_accuracy:.1f}% ({stage_accurate}/{len(stage_cases)})"
            )

    # Print empathy adaptation summary
    empathy_adaptations = {}
    for analysis in all_behavioral_analyses:
        if "EMPATHY_NEEDS:" in analysis["analysis"]:
            empathy_need = (
                analysis["analysis"].split("EMPATHY_NEEDS:")[1].strip()[:50] + "..."
            )
            empathy_adaptations[empathy_need] = (
                empathy_adaptations.get(empathy_need, 0) + 1
            )

    print("\n💝 Top Empathy Adaptations Used:")
    sorted_adaptations = sorted(
        empathy_adaptations.items(), key=lambda x: x[1], reverse=True
    )
    for adaptation, count in sorted_adaptations[:5]:
        print(f"  {adaptation}: {count} times")


def calculate_accuracy_score(found, position, total_predictions):
    """Calculate accuracy score based on whether gold diagnosis was found and its position"""
    if not found:
        return 0.0

    # Higher score for earlier positions
    if position == 1:
        return 1.0
    elif position <= 3:
        return 0.8
    elif position <= 5:
        return 0.6
    else:
        return 0.4


def load_vignettes(filename, desired_types=None):
    """Load vignettes from JSON file"""
    with open(filename, "r") as f:
        data = json.load(f)
    
    flattened_vignettes = []
    
    if desired_types is None:
        desired_types = ["typical", "severe"]
    
    # Handle roleplay scripts structure
    if "roleplay_scripts" in data:
        roleplay_dict = data["roleplay_scripts"]
        for disease, scripts in roleplay_dict.items():
            # Only process if we have a list of scripts
            if not isinstance(scripts, list):
                continue

            # Select specific types
            selected_scripts = []
            for script in scripts:
                if isinstance(script, dict) and "variation_type" in script:
                    if script["variation_type"] in desired_types:
                        selected_scripts.append(script)
                else:
                    # If no variation_type, include it (fallback)
                    selected_scripts.append(script)

            # Limit to 2 even from selected types
            limited_scripts = selected_scripts[:2]

            for script in limited_scripts:
                # Extract the roleplay_script content as the vignette text
                if isinstance(script, dict) and "roleplay_script" in script:
                    flattened_vignettes.append((disease, script["roleplay_script"]))
                else:
                    # Fallback if script is just a string
                    flattened_vignettes.append((disease, str(script)))

            print(
                f"   {disease}: Selected {len(limited_scripts)} vignettes ({[s.get('variation_type', 'unknown') for s in limited_scripts]})"
            )
    else:
        raise ValueError(
            f"Expected 'roleplay_scripts' key in JSON structure. Found keys: {list(data.keys()) if isinstance(data, dict) else type(data)}"
        )
    
    return flattened_vignettes
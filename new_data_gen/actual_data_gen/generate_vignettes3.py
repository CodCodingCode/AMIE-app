# 100-Disease Training Dataset for Medical AI
priority_diseases = {
    "common_primary_care": 50,  # 2x from 25
    "emergency_conditions": 30,  # 2x from 15
    "commonly_misdiagnosed": 20,  # 2x from 10
}

# ===== COMMON PRIMARY CARE (50 diseases) =====
common_primary_care = [
    # Cardiovascular (12)
    "Hypertension",
    "Diabetes Mellitus, Type 2",
    "Diabetes Mellitus, Type 1",
    "Hyperlipidemia",
    "Atrial Fibrillation",
    "Heart Failure",
    "Coronary Artery Disease",
    "Peripheral Artery Disease",
    "Venous Thromboembolism",
    "Varicose Veins",
    "Mitral Valve Prolapse",
    "Hypertensive Heart Disease",
    # Respiratory (8)
    "Asthma",
    "COPD",
    "Upper Respiratory Infection",
    "Bronchitis",
    "Allergic Rhinitis",
    "Sinusitis",
    "Sleep Apnea",
    "Chronic Cough",
    # Gastrointestinal (8)
    "Gastroesophageal Reflux Disease",
    "Peptic Ulcer Disease",
    "Irritable Bowel Syndrome",
    "Gastroenteritis",
    "Constipation",
    "Hemorrhoids",
    "Diverticulosis",
    "Gallstones",
    # Musculoskeletal (6)
    "Osteoarthritis",
    "Low Back Pain",
    "Rheumatoid Arthritis",
    "Osteoporosis",
    "Gout",
    "Carpal Tunnel Syndrome",
    # Mental Health (5)
    "Depression",
    "Anxiety Disorders",
    "Panic Disorder",
    "Insomnia",
    "Bipolar Disorder",
    # Endocrine (4)
    "Hypothyroidism",
    "Hyperthyroidism",
    "Metabolic Syndrome",
    "Obesity",
    # Dermatologic (3)
    "Eczema",
    "Psoriasis",
    "Acne",
    # Urologic/Reproductive (4)
    "Urinary Tract Infection",
    "Benign Prostatic Hyperplasia",
    "Kidney Stones",
    "Erectile Dysfunction",
]

# ===== EMERGENCY CONDITIONS (30 diseases) =====
emergency_conditions = [
    # Cardiovascular Emergencies (8)
    "Myocardial Infarction",
    "Acute Coronary Syndrome",
    "Pulmonary Embolism",
    "Aortic Dissection",
    "Cardiac Arrest",
    "Hypertensive Crisis",
    "Acute Heart Failure",
    "Pericarditis",
    # Neurological Emergencies (7)
    "Stroke",
    "Transient Ischemic Attack",
    "Subarachnoid Hemorrhage",
    "Meningitis",
    "Encephalitis",
    "Status Epilepticus",
    "Acute Spinal Cord Injury",
    # Respiratory Emergencies (5)
    "Pneumonia",
    "Acute Asthma Exacerbation",
    "Pneumothorax",
    "Acute Respiratory Distress Syndrome",
    "Anaphylaxis",
    # Gastrointestinal Emergencies (5)
    "Appendicitis",
    "Acute Cholangitis",
    "Gastrointestinal Bleeding",
    "Bowel Obstruction",
    "Acute Pancreatitis",
    # Infectious/Systemic (3)
    "Sepsis",
    "Septic Shock",
    "Diabetic Ketoacidosis",
    # Trauma/Other (2)
    "Acute Abdomen",
    "Ectopic Pregnancy",
]

# ===== COMMONLY MISDIAGNOSED (20 diseases) =====
commonly_misdiagnosed = [
    # Autoimmune/Rheumatologic (6)
    "Systemic Lupus Erythematosus",
    "Fibromyalgia",
    "Multiple Sclerosis",
    "Polymyalgia Rheumatica",
    "Giant Cell Arteritis",
    "Sjogren's Syndrome",
    # Endocrine (4)
    "Adrenal Insufficiency",
    "Diabetes Insipidus",
    "Polycystic Ovary Syndrome",
    "Cushing's Syndrome",
    # Psychiatric presenting as medical (3)
    "Conversion Disorder",
    "Somatization Disorder",
    "Chronic Fatigue Syndrome",
    # Infectious (2)
    "Lyme Disease",
    "Tuberculosis",
    # Gastrointestinal (3)
    "Celiac Disease",
    "Inflammatory Bowel Disease",
    "Gastroparesis",
    # Neurological (2)
    "Migraine",
    "Trigeminal Neuralgia",
]


# ===== COMPLETE DATASET SUMMARY =====
def print_dataset_summary():
    print("🏥 MEDICAL AI TRAINING DATASET - 100 DISEASES")
    print("=" * 60)

    print(f"\n📊 DATASET BREAKDOWN:")
    print(f"   Common Primary Care: {len(common_primary_care)} diseases")
    print(f"   Emergency Conditions: {len(emergency_conditions)} diseases")
    print(f"   Commonly Misdiagnosed: {len(commonly_misdiagnosed)} diseases")
    print(
        f"   TOTAL: {len(common_primary_care) + len(emergency_conditions) + len(commonly_misdiagnosed)} diseases"
    )

    print(f"\n🎯 TRAINING DATA ESTIMATES:")
    print(f"   4-5 conversations per disease = 400-500 total conversations")
    print(f"   Multiple patient behaviors per disease")
    print(f"   Comprehensive diagnostic reasoning coverage")

    print(f"\n📈 CLINICAL COVERAGE:")
    print(f"   ✅ Primary care (80% of patient encounters)")
    print(f"   ✅ Emergency medicine (high-stakes decisions)")
    print(f"   ✅ Complex diagnostics (challenging cases)")
    print(f"   ✅ Multi-specialty representation")


# ===== EXPORT FUNCTIONS =====
def get_all_diseases():
    """Return complete list of all 100 diseases"""
    return common_primary_care + emergency_conditions + commonly_misdiagnosed


def get_diseases_by_category():
    """Return diseases organized by category"""
    return {
        "common_primary_care": common_primary_care,
        "emergency_conditions": emergency_conditions,
        "commonly_misdiagnosed": commonly_misdiagnosed,
    }


def export_to_json(filename="medical_training_diseases_100.json"):
    """Export dataset to JSON file"""
    import json

    dataset = {
        "metadata": {
            "total_diseases": len(get_all_diseases()),
            "categories": {
                "common_primary_care": len(common_primary_care),
                "emergency_conditions": len(emergency_conditions),
                "commonly_misdiagnosed": len(commonly_misdiagnosed),
            },
            "description": "Curated 100-disease dataset for medical AI training",
            "version": "1.0",
        },
        "diseases_by_category": get_diseases_by_category(),
        "all_diseases": get_all_diseases(),
    }

    with open(filename, "w") as f:
        json.dump(dataset, f, indent=2)

    print(f"💾 Dataset exported to {filename}")


# ===== DISEASE VALIDATION =====
def validate_dataset():
    """Check for duplicates and validate dataset integrity"""
    all_diseases = get_all_diseases()

    # Check for duplicates
    duplicates = []
    seen = set()
    for disease in all_diseases:
        if disease in seen:
            duplicates.append(disease)
        seen.add(disease)

    print(f"\n🔍 DATASET VALIDATION:")
    print(f"   Total unique diseases: {len(seen)}")
    print(f"   Expected diseases: 100")
    print(f"   Duplicates found: {len(duplicates)}")

    if duplicates:
        print(f"   ⚠️  Duplicate diseases: {duplicates}")
    else:
        print(f"   ✅ No duplicates found")

    # Check category counts
    expected_counts = {
        "common_primary_care": 50,
        "emergency_conditions": 30,
        "commonly_misdiagnosed": 20,
    }
    actual_counts = {
        cat: len(diseases) for cat, diseases in get_diseases_by_category().items()
    }

    print(f"\n📊 CATEGORY VALIDATION:")
    for category, expected in expected_counts.items():
        actual = actual_counts[category]
        status = "✅" if actual == expected else "⚠️"
        print(f"   {status} {category}: {actual}/{expected}")


# ===== USAGE EXAMPLES =====
if __name__ == "__main__":
    # Print summary
    print_dataset_summary()

    # Validate dataset
    validate_dataset()

    # Export to JSON
    export_to_json()

    print(f"\n🚀 READY FOR TRAINING!")
    print(f"   Use get_all_diseases() to get the complete list")
    print(f"   Use get_diseases_by_category() for organized access")
    print(f"   Dataset covers major medical specialties and complexity levels")

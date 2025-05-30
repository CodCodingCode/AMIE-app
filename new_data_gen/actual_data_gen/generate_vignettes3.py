import os
import json
import time
import random
from openai import OpenAI
from typing import Dict, List, Any
import multiprocessing
from concurrent.futures import ThreadPoolExecutor
import threading

# Initialize OpenAI client
client = OpenAI(api_key="your_api_key_here")  # Replace with your actual API key
model = "gpt-4o"  # Using GPT-4 for highest quality medical vignettes

# Your 100-disease dataset
common_primary_care = [
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
    "Asthma",
    "COPD",
    "Upper Respiratory Infection",
    "Bronchitis",
    "Allergic Rhinitis",
    "Sinusitis",
    "Sleep Apnea",
    "Chronic Cough",
    "Gastroesophageal Reflux Disease",
    "Peptic Ulcer Disease",
    "Irritable Bowel Syndrome",
    "Gastroenteritis",
    "Constipation",
    "Hemorrhoids",
    "Diverticulosis",
    "Gallstones",
    "Osteoarthritis",
    "Low Back Pain",
    "Rheumatoid Arthritis",
    "Osteoporosis",
    "Gout",
    "Carpal Tunnel Syndrome",
    "Depression",
    "Anxiety Disorders",
    "Panic Disorder",
    "Insomnia",
    "Bipolar Disorder",
    "Hypothyroidism",
    "Hyperthyroidism",
    "Metabolic Syndrome",
    "Obesity",
    "Eczema",
    "Psoriasis",
    "Acne",
    "Urinary Tract Infection",
    "Benign Prostatic Hyperplasia",
    "Kidney Stones",
    "Erectile Dysfunction",
]

emergency_conditions = [
    "Myocardial Infarction",
    "Acute Coronary Syndrome",
    "Pulmonary Embolism",
    "Aortic Dissection",
    "Cardiac Arrest",
    "Hypertensive Crisis",
    "Acute Heart Failure",
    "Pericarditis",
    "Stroke",
    "Transient Ischemic Attack",
    "Subarachnoid Hemorrhage",
    "Meningitis",
    "Encephalitis",
    "Status Epilepticus",
    "Acute Spinal Cord Injury",
    "Pneumonia",
    "Acute Asthma Exacerbation",
    "Pneumothorax",
    "Acute Respiratory Distress Syndrome",
    "Anaphylaxis",
    "Appendicitis",
    "Acute Cholangitis",
    "Gastrointestinal Bleeding",
    "Bowel Obstruction",
    "Acute Pancreatitis",
    "Sepsis",
    "Septic Shock",
    "Diabetic Ketoacidosis",
    "Acute Abdomen",
    "Ectopic Pregnancy",
]

commonly_misdiagnosed = [
    "Systemic Lupus Erythematosus",
    "Fibromyalgia",
    "Multiple Sclerosis",
    "Polymyalgia Rheumatica",
    "Giant Cell Arteritis",
    "Sjogren's Syndrome",
    "Adrenal Insufficiency",
    "Diabetes Insipidus",
    "Polycystic Ovary Syndrome",
    "Cushing's Syndrome",
    "Conversion Disorder",
    "Somatization Disorder",
    "Chronic Fatigue Syndrome",
    "Lyme Disease",
    "Tuberculosis",
    "Celiac Disease",
    "Inflammatory Bowel Disease",
    "Gastroparesis",
    "Migraine",
    "Trigeminal Neuralgia",
]


def get_all_diseases():
    """Return complete list of all 100 diseases"""
    return common_primary_care + emergency_conditions + commonly_misdiagnosed


class VignetteGenerator:
    def __init__(self, api_key: str, model: str = "gpt-4.1-nano"):
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.request_count = 0
        self.request_lock = threading.Lock()

    def rate_limit_delay(self):
        """Simple rate limiting to avoid hitting API limits"""
        with self.request_lock:
            self.request_count += 1
            if self.request_count % 50 == 0:  # Every 50 requests
                print(f"🕐 Rate limiting... Processed {self.request_count} requests")
                time.sleep(10)  # 10 second pause
            else:
                time.sleep(0.5)  # Small delay between requests

    def generate_vignette(self, disease: str, vignette_number: int) -> str:
        """Generate a single detailed patient vignette for a given disease"""

        # Determine category for context
        category = self._get_disease_category(disease)

        # Create specialized prompts based on category
        prompt = self._create_disease_specific_prompt(
            disease, category, vignette_number
        )

        try:
            self.rate_limit_delay()

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a board-certified physician and medical educator specializing in creating realistic, detailed patient vignettes for medical training. Your vignettes should be clinically accurate, educationally valuable, and represent real-world presentations.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.8,  # Some creativity for realistic variation
                max_tokens=800,  # Detailed vignettes
            )

            vignette = response.choices[0].message.content.strip()

            # Validate and clean the vignette
            validated_vignette = self._validate_vignette(vignette, disease)

            print(f"✅ Generated vignette {vignette_number} for {disease}")
            return validated_vignette

        except Exception as e:
            print(f"❌ Error generating vignette for {disease}: {str(e)}")
            return self._create_fallback_vignette(disease, vignette_number)

    def _get_disease_category(self, disease: str) -> str:
        """Determine which category a disease belongs to"""
        if disease in common_primary_care:
            return "primary_care"
        elif disease in emergency_conditions:
            return "emergency"
        elif disease in commonly_misdiagnosed:
            return "misdiagnosed"
        else:
            return "general"

    def _create_disease_specific_prompt(
        self, disease: str, category: str, vignette_number: int
    ) -> str:
        """Create a specialized prompt based on disease and category"""

        base_requirements = f"""
        Create a detailed, realistic patient vignette for: {disease}
        
        REQUIREMENTS:
        - Include specific age, gender, and relevant demographics
        - Describe presenting symptoms in realistic, patient-like language
        - Include relevant medical history, family history, and social history
        - Mention physical examination findings when appropriate
        - Include timeline of symptom development
        - Make it sound like a real patient encounter, not a textbook
        - Vary the presentation style (some patients are detailed, others vague)
        - Include both typical and some atypical presentations
        - Length: 150-250 words
        
        MEDICAL ACCURACY REQUIREMENTS:
        - Symptoms must be consistent with {disease}
        - Include relevant risk factors and epidemiology
        - Mention appropriate associated symptoms
        - Include red flags or complications when relevant
        """

        # Category-specific additions
        if category == "emergency":
            category_prompt = f"""
            EMERGENCY CONTEXT:
            - Emphasize acute onset and severity
            - Include time-critical symptoms
            - Mention vital signs abnormalities where relevant
            - Include patient or family urgency/concern
            - Describe symptoms that brought patient to emergency care
            """
        elif category == "primary_care":
            category_prompt = f"""
            PRIMARY CARE CONTEXT:
            - Focus on chronic or subacute presentation
            - Include impact on daily activities
            - Mention previous attempts at self-management
            - Include relevant lifestyle factors
            - Show gradual progression or intermittent symptoms
            """
        elif category == "misdiagnosed":
            category_prompt = f"""
            CHALLENGING DIAGNOSIS CONTEXT:
            - Include symptoms that could suggest other conditions
            - Mention previous medical encounters or misdiagnoses
            - Include vague or atypical presentations
            - Add complexity with overlapping symptoms
            - Show diagnostic uncertainty or delays
            """
        else:
            category_prompt = ""

        # Variation prompts for multiple vignettes
        variation_prompts = [
            "Create a typical presentation that most medical students would recognize.",
            "Create an atypical presentation that might be more challenging to diagnose.",
            "Create a presentation in an elderly patient with comorbidities.",
            "Create a presentation in a younger patient with an unusual risk profile.",
            "Create a presentation with concurrent symptoms that might confuse the diagnosis.",
        ]

        variation_prompt = variation_prompts[vignette_number % len(variation_prompts)]

        return f"{base_requirements}\n{category_prompt}\n\nVARIATION: {variation_prompt}\n\nGenerate the patient vignette now:"

    def _validate_vignette(self, vignette: str, disease: str) -> str:
        """Validate and clean the generated vignette"""
        # Remove any unwanted prefixes or formatting
        vignette = vignette.replace("**", "").replace("##", "")

        # Ensure it starts appropriately
        if not any(
            vignette.startswith(prefix)
            for prefix in ["A ", "The ", "This ", f"A {vignette.split()[0]}"]
        ):
            vignette = f"A {vignette}"

        # Ensure reasonable length
        if len(vignette) < 100:
            print(f"⚠️ Short vignette for {disease}, might need regeneration")

        return vignette.strip()

    def _create_fallback_vignette(self, disease: str, vignette_number: int) -> str:
        """Create a basic fallback vignette if API call fails"""
        return f"A patient presents with symptoms consistent with {disease}. This case requires further development due to generation error. (Vignette {vignette_number})"


def generate_vignettes_for_disease(args):
    """Generate multiple vignettes for a single disease (for multiprocessing)"""
    disease, num_vignettes, api_key, model = args
    generator = VignetteGenerator(api_key, model)

    vignettes = []
    for i in range(num_vignettes):
        try:
            vignette = generator.generate_vignette(disease, i + 1)
            vignettes.append(vignette)
        except Exception as e:
            print(f"❌ Failed to generate vignette {i+1} for {disease}: {e}")
            vignettes.append(generator._create_fallback_vignette(disease, i + 1))

    return disease, vignettes


def generate_all_vignettes(
    api_key: str,
    num_vignettes_per_disease: int = 4,
    output_file: str = "medical_vignettes_100_diseases.json",
    max_workers: int = 5,
):
    """Generate vignettes for all 100 diseases"""

    all_diseases = get_all_diseases()
    print(
        f"🏥 Generating {num_vignettes_per_disease} vignettes for {len(all_diseases)} diseases"
    )
    print(
        f"📊 Total vignettes to generate: {len(all_diseases) * num_vignettes_per_disease}"
    )

    # Prepare arguments for multiprocessing
    args_list = [
        (disease, num_vignettes_per_disease, api_key, "gpt-4o")
        for disease in all_diseases
    ]

    # Use ThreadPoolExecutor for API calls (better for I/O bound tasks)
    results = {}
    completed = 0

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_disease = {
            executor.submit(generate_vignettes_for_disease, args): args[0]
            for args in args_list
        }

        for future in future_to_disease:
            try:
                disease, vignettes = future.result(timeout=300)  # 5 minute timeout
                results[disease] = vignettes
                completed += 1

                progress = (completed / len(all_diseases)) * 100
                print(
                    f"📈 Progress: {completed}/{len(all_diseases)} diseases completed ({progress:.1f}%)"
                )

            except Exception as e:
                disease = future_to_disease[future]
                print(f"❌ Failed to generate vignettes for {disease}: {e}")
                results[disease] = [
                    f"Error generating vignettes for {disease}"
                ] * num_vignettes_per_disease

    # Save results
    output_data = {
        "metadata": {
            "total_diseases": len(all_diseases),
            "vignettes_per_disease": num_vignettes_per_disease,
            "total_vignettes": len(all_diseases) * num_vignettes_per_disease,
            "generation_model": "gpt-4o",
            "categories": {
                "common_primary_care": len(common_primary_care),
                "emergency_conditions": len(emergency_conditions),
                "commonly_misdiagnosed": len(commonly_misdiagnosed),
            },
        },
        "vignettes": results,
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Completed! Generated vignettes saved to: {output_file}")

    # Summary statistics
    total_vignettes = sum(len(vignettes) for vignettes in results.values())
    successful_diseases = sum(
        1 for vignettes in results.values() if not any("Error" in v for v in vignettes)
    )

    print(f"\n📊 GENERATION SUMMARY:")
    print(f"   Total diseases: {len(all_diseases)}")
    print(f"   Successful diseases: {successful_diseases}")
    print(f"   Total vignettes generated: {total_vignettes}")
    print(f"   Average vignettes per disease: {total_vignettes/len(all_diseases):.1f}")

    return results


def validate_generated_vignettes(results_file: str):
    """Validate the quality of generated vignettes"""
    with open(results_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    vignettes = data["vignettes"]

    print("\n🔍 VIGNETTE QUALITY VALIDATION:")

    # Check for errors
    error_count = 0
    short_count = 0
    good_count = 0

    for disease, disease_vignettes in vignettes.items():
        for vignette in disease_vignettes:
            if "Error" in vignette or "error" in vignette:
                error_count += 1
            elif len(vignette) < 100:
                short_count += 1
            else:
                good_count += 1

    total = error_count + short_count + good_count

    print(f"   ✅ Good quality vignettes: {good_count} ({good_count/total*100:.1f}%)")
    print(f"   ⚠️ Short vignettes: {short_count} ({short_count/total*100:.1f}%)")
    print(f"   ❌ Error vignettes: {error_count} ({error_count/total*100:.1f}%)")

    # Show some examples
    print(f"\n📋 SAMPLE VIGNETTES:")
    sample_diseases = list(vignettes.keys())[:3]
    for disease in sample_diseases:
        print(f"\n{disease}:")
        print(f"   {vignettes[disease][0][:150]}...")


if __name__ == "__main__":
    # Configuration
    API_KEY = "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"  # Replace with your actual API key
    NUM_VIGNETTES_PER_DISEASE = 7  # Generate 4 vignettes per disease
    OUTPUT_FILE = "medical_vignettes_100_diseases.json"
    MAX_WORKERS = 12  # Adjust based on your API rate limits

    print("🏥 MEDICAL VIGNETTE GENERATOR")
    print("=" * 50)

    # Generate vignettes
    results = generate_all_vignettes(
        api_key=API_KEY,
        num_vignettes_per_disease=NUM_VIGNETTES_PER_DISEASE,
        output_file=OUTPUT_FILE,
        max_workers=MAX_WORKERS,
    )

    # Validate results
    validate_generated_vignettes(OUTPUT_FILE)

    print(
        f"\n🚀 Ready for training! Use {OUTPUT_FILE} as input for your conversation generation pipeline."
    )

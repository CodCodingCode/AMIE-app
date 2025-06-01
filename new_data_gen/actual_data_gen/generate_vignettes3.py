import os
import json
import time
import random
from openai import OpenAI
from typing import Dict, List, Any, Optional
import multiprocessing
from concurrent.futures import ThreadPoolExecutor
import threading

# Initialize OpenAI client
client = OpenAI(
    api_key="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"
)
model = "gpt-4.1-nano"


class MedicallyAccurateVignetteGenerator:
    def __init__(self, api_key: str, model: str = "gpt-4.1-nano"):
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.request_count = 0
        self.request_lock = threading.Lock()

    def load_medical_data(self, json_file_path: str) -> List[Dict]:
        """Load medical disease data from JSON file"""
        try:
            with open(json_file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if isinstance(data, list):
                print(f"✅ Loaded {len(data)} diseases from {json_file_path}")
                return data
            elif isinstance(data, dict) and "diseases" in data:
                diseases = data["diseases"]
                print(f"✅ Loaded {len(diseases)} diseases from {json_file_path}")
                return diseases
            else:
                print(f"❌ Unexpected JSON structure in {json_file_path}")
                return []
        except Exception as e:
            print(f"❌ Error loading medical data: {e}")
            return []

    def rate_limit_delay(self):
        """Rate limiting to avoid hitting API limits"""
        with self.request_lock:
            self.request_count += 1
            if self.request_count % 50 == 0:
                print(f"🕐 Rate limiting... Processed {self.request_count} requests")
                time.sleep(15)
            else:
                time.sleep(0.7)

    def generate_vignette_with_medical_data(
        self, disease_data: Dict, vignette_number: int, variation_type: str = "typical"
    ) -> str:
        """Generate a medically accurate vignette using the JSON data"""

        disease_name = disease_data.get("disease_name", "Unknown Disease")

        # Create medically accurate prompt
        prompt = self._create_medically_accurate_prompt(
            disease_data, vignette_number, variation_type
        )

        try:
            self.rate_limit_delay()

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": """You are a board-certified physician and medical educator. Create realistic patient vignettes that are:
                        - MEDICALLY ACCURATE - respect disease demographics, age/gender patterns, and typical presentations
                        - EDUCATIONALLY VALUABLE - show realistic symptom patterns and patient presentations
                        - CLINICALLY AUTHENTIC - written from actual patient encounters
                        
                        CRITICAL: Always respect medical accuracy over demographic diversity. If a disease primarily affects women, create female patients. If it affects elderly patients, use appropriate age ranges.""",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,  # Balanced creativity with accuracy
                max_tokens=800,
            )

            vignette = response.choices[0].message.content.strip()
            validated_vignette = self._validate_vignette(vignette, disease_name)

            print(
                f"✅ Generated {variation_type} vignette {vignette_number} for {disease_name}"
            )
            return validated_vignette

        except Exception as e:
            print(f"❌ Error generating vignette for {disease_name}: {str(e)}")
            return self._create_fallback_vignette(disease_data, vignette_number)

    def _create_medically_accurate_prompt(
        self, disease_data: Dict, vignette_number: int, variation_type: str
    ) -> str:
        """Create a medically accurate prompt that respects disease demographics"""

        disease_name = disease_data.get("disease_name", "Unknown Disease")
        symptoms = disease_data.get("symptoms", [])
        causes = disease_data.get("causes", [])
        risk_factors = disease_data.get("risk_factors", [])
        prognosis = disease_data.get("prognosis", "")

        # Select different symptom combinations for variation
        if variation_type == "typical":
            # Most common presentation
            selected_symptoms = symptoms[:5] if len(symptoms) >= 5 else symptoms
        elif variation_type == "early":
            # Early/mild presentation
            selected_symptoms = symptoms[:3] if len(symptoms) >= 3 else symptoms
        elif variation_type == "severe":
            # More severe presentation with complications
            selected_symptoms = symptoms[:7] if len(symptoms) >= 7 else symptoms
        else:  # mixed
            # Mixed presentation
            if len(symptoms) >= 6:
                selected_symptoms = symptoms[:2] + symptoms[3:6]
            else:
                selected_symptoms = symptoms

        # Medical accuracy instructions
        medical_accuracy_note = self._get_medical_accuracy_instructions(
            disease_name, risk_factors
        )

        base_prompt = f"""
        Create a realistic patient vignette for: {disease_name}

        MEDICAL DATA TO INCORPORATE:
        Symptoms to include: {', '.join(selected_symptoms)}
        Risk factors: {', '.join(risk_factors[:4])}
        Underlying causes: {', '.join(causes[:3])}
        {f"Clinical context: {prognosis[:150]}..." if prognosis else ""}

        MEDICAL ACCURACY REQUIREMENTS:
        {medical_accuracy_note}

        VIGNETTE REQUIREMENTS:
        - Create a realistic patient presentation (200-250 words)
        - Use appropriate demographics for this specific disease
        - Include specific age and gender that match typical disease patterns
        - Present symptoms in natural patient language (not medical jargon)
        - Include realistic timeline of symptom development
        - Mention relevant medical/family/social history
        - Show what prompted the patient to seek care
        - Include realistic patient concerns

        VARIATION TYPE: {variation_type.upper()}
        """

        # Add variation-specific instructions
        if variation_type == "typical":
            variation_instructions = """
            - Create a classic, textbook presentation
            - Include the most common symptoms for this disease
            - Use typical demographics and risk factors
            - Show clear progression that leads to diagnosis
            """
        elif variation_type == "early":
            variation_instructions = """
            - Create an early-stage or mild presentation
            - Show fewer symptoms or less severe manifestations
            - Patient may be uncertain about seeking care
            - Symptoms may be developing gradually
            """
        elif variation_type == "severe":
            variation_instructions = """
            - Create a more advanced or complicated presentation
            - Include additional symptoms or complications
            - Show more urgent or concerning features
            - Patient may have delayed seeking care
            """
        else:  # mixed
            variation_instructions = """
            - Create a mixed presentation with varying symptom severity
            - Include both early and more developed symptoms
            - Show realistic complexity in symptom pattern
            - May include some atypical features
            """

        return f"{base_prompt}\n{variation_instructions}\n\nGenerate the medically accurate patient vignette:"

    def _get_medical_accuracy_instructions(
        self, disease_name: str, risk_factors: List[str]
    ) -> str:
        """Generate specific medical accuracy instructions based on disease and risk factors"""

        instructions = []

        # Gender-specific diseases
        if any(
            term in disease_name.lower()
            for term in [
                "pregnancy",
                "postpartum",
                "peripartum",
                "maternal",
                "ovarian",
                "cervical",
                "endometrial",
                "uterine",
                "breast cancer",
                "pcos",
                "polycystic ovary",
            ]
        ):
            instructions.append(
                "- MUST use female patient - this disease affects women"
            )

        elif any(
            term in disease_name.lower()
            for term in ["prostate", "testicular", "erectile", "male pattern"]
        ):
            instructions.append("- MUST use male patient - this disease affects men")

        # Age-specific considerations
        if any(
            term in disease_name.lower()
            for term in [
                "perinatal",
                "neonatal",
                "pediatric",
                "childhood",
                "congenital",
            ]
        ):
            instructions.append(
                "- Use appropriate pediatric age range (newborn to 18 years)"
            )

        elif any(
            term in disease_name.lower()
            for term in ["geriatric", "age-related", "senile", "elderly"]
        ):
            instructions.append(
                "- Use elderly patient (65+ years) - this disease is age-related"
            )

        # Risk factor analysis
        for rf in risk_factors[:3]:  # Check first 3 risk factors
            rf_lower = rf.lower()

            if "female" in rf_lower or "women" in rf_lower:
                instructions.append("- Prefer female patient based on risk factors")
            elif "male" in rf_lower or "men" in rf_lower:
                instructions.append("- Prefer male patient based on risk factors")

            if "age" in rf_lower and any(
                age_term in rf_lower for age_term in ["older", "elderly", ">", "above"]
            ):
                instructions.append(
                    "- Use older patient (50+ years) based on age-related risk"
                )
            elif "young" in rf_lower or "adolescent" in rf_lower:
                instructions.append("- Use younger patient based on risk factors")

            if "pregnancy" in rf_lower or "postpartum" in rf_lower:
                instructions.append("- MUST use female patient of childbearing age")

        # Default instruction if no specific requirements
        if not instructions:
            instructions.append(
                "- Use demographics that are medically appropriate for this condition"
            )
            instructions.append(
                "- Consider typical age and gender patterns for this disease"
            )

        return "\n".join(instructions)

    def _validate_vignette(self, vignette: str, disease_name: str) -> str:
        """Clean and validate the generated vignette"""
        # Remove formatting
        vignette = vignette.replace("**", "").replace("##", "").replace("***", "")

        # Remove meta-commentary
        lines = vignette.split("\n")
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            if line and not any(
                phrase in line.lower()
                for phrase in [
                    "this vignette",
                    "this case",
                    "note:",
                    "summary:",
                    "diagnosis:",
                ]
            ):
                cleaned_lines.append(line)

        vignette = "\n".join(cleaned_lines)

        # Ensure proper starting
        if not any(
            vignette.startswith(prefix)
            for prefix in ["A ", "The ", "This ", "Ms.", "Mr.", "Mrs."]
        ):
            vignette = f"A {vignette}"

        return vignette.strip()

    def _create_fallback_vignette(
        self, disease_data: Dict, vignette_number: int
    ) -> str:
        """Create a basic fallback vignette if API call fails"""
        disease_name = disease_data.get("disease_name", "Unknown Disease")
        symptoms = disease_data.get("symptoms", [])

        basic_symptoms = symptoms[:3] if symptoms else ["various symptoms"]

        return f"""A patient presents with {', '.join(basic_symptoms[:2])} and {basic_symptoms[2] if len(basic_symptoms) > 2 else 'related symptoms'}. The patient reports these symptoms have been concerning them and affecting their daily activities. Medical evaluation is being sought for proper diagnosis and management of {disease_name}. (Fallback vignette {vignette_number})"""


def generate_vignettes_for_disease_with_data(args):
    """Generate multiple medically accurate vignettes for a single disease"""
    disease_data, num_vignettes, api_key, model = args
    generator = MedicallyAccurateVignetteGenerator(api_key, model)

    disease_name = disease_data.get("disease_name", "Unknown Disease")

    # Variation types focused on medical presentation, not demographics
    variation_types = ["typical", "early", "severe", "mixed"]

    vignettes = []
    for i in range(num_vignettes):
        try:
            variation_type = variation_types[i % len(variation_types)]
            vignette = generator.generate_vignette_with_medical_data(
                disease_data, i + 1, variation_type
            )
            vignettes.append(
                {
                    "vignette": vignette,
                    "variation_type": variation_type,
                    "vignette_number": i + 1,
                }
            )
        except Exception as e:
            print(f"❌ Failed to generate vignette {i+1} for {disease_name}: {e}")
            vignettes.append(
                {
                    "vignette": generator._create_fallback_vignette(
                        disease_data, i + 1
                    ),
                    "variation_type": "fallback",
                    "vignette_number": i + 1,
                }
            )

    return disease_name, vignettes


def generate_vignettes_from_medical_json(
    medical_json_file: str,
    api_key: str,
    num_vignettes_per_disease: int = 2,
    output_file: str = "medically_accurate_vignettes.json",
    max_workers: int = 12,
):
    """Generate medically accurate vignettes from medical JSON data"""

    generator = MedicallyAccurateVignetteGenerator(api_key, model)
    medical_data = generator.load_medical_data(medical_json_file)

    if not medical_data:
        print("❌ No medical data loaded. Exiting.")
        return {}

    print(
        f"🏥 Generating {num_vignettes_per_disease} MEDICALLY ACCURATE vignettes for {len(medical_data)} diseases"
    )
    print(
        f"📊 Total vignettes to generate: {len(medical_data) * num_vignettes_per_disease}"
    )

    args_list = [
        (disease_data, num_vignettes_per_disease, api_key, model)
        for disease_data in medical_data
    ]

    results = {}
    completed = 0

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_disease = {
            executor.submit(generate_vignettes_for_disease_with_data, args): args[
                0
            ].get("disease_name", f"Disease_{i}")
            for i, args in enumerate(args_list)
        }

        for future in future_to_disease:
            try:
                disease_name, vignettes = future.result(timeout=600)
                results[disease_name] = vignettes
                completed += 1

                progress = (completed / len(medical_data)) * 100
                print(
                    f"📈 Progress: {completed}/{len(medical_data)} diseases completed ({progress:.1f}%)"
                )

            except Exception as e:
                disease_name = future_to_disease[future]
                print(f"❌ Failed to generate vignettes for {disease_name}: {e}")
                fallback_vignettes = []
                for i in range(num_vignettes_per_disease):
                    fallback_vignettes.append(
                        {
                            "vignette": f"Error generating vignette for {disease_name} (vignette {i+1})",
                            "variation_type": "error",
                            "vignette_number": i + 1,
                        }
                    )
                results[disease_name] = fallback_vignettes

    # Save results
    output_data = {
        "metadata": {
            "source_file": medical_json_file,
            "total_diseases": len(medical_data),
            "vignettes_per_disease": num_vignettes_per_disease,
            "total_vignettes": len(medical_data) * num_vignettes_per_disease,
            "generation_model": model,
            "variation_types": ["typical", "early", "severe", "mixed"],
            "generation_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "focus": "medically_accurate_presentations",
        },
        "vignettes": results,
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Completed! Medically accurate vignettes saved to: {output_file}")

    # Summary statistics
    total_vignettes = sum(len(vignettes) for vignettes in results.values())
    successful_diseases = sum(
        1
        for vignettes in results.values()
        if not any("Error" in v.get("vignette", "") for v in vignettes)
    )

    print(f"\n📊 GENERATION SUMMARY:")
    print(f"   Total diseases processed: {len(medical_data)}")
    print(f"   Successful diseases: {successful_diseases}")
    print(f"   Total vignettes generated: {total_vignettes}")
    print(f"   Medical accuracy prioritized over demographic diversity")

    return results


if __name__ == "__main__":
    # Configuration
    API_KEY = "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"
    MEDICAL_JSON_FILE = "combined.json"
    NUM_VIGNETTES_PER_DISEASE = 2
    OUTPUT_FILE = "medically_accurate_vignettes.json"
    MAX_WORKERS = 12

    print("🏥 MEDICALLY ACCURATE VIGNETTE GENERATOR")
    print("=" * 50)
    print("🎯 Prioritizing medical accuracy over demographic diversity")

    if not os.path.exists(MEDICAL_JSON_FILE):
        print(f"❌ Medical JSON file not found: {MEDICAL_JSON_FILE}")
        exit(1)

    results = generate_vignettes_from_medical_json(
        medical_json_file=MEDICAL_JSON_FILE,
        api_key=API_KEY,
        num_vignettes_per_disease=NUM_VIGNETTES_PER_DISEASE,
        output_file=OUTPUT_FILE,
        max_workers=MAX_WORKERS,
    )

    print(f"\n🚀 Ready for training! Medically accurate vignettes in: {OUTPUT_FILE}")

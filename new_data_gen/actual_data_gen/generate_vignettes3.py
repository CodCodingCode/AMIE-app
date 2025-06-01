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
    api_key="api"
)  # Replace with your actual API key
model = "gpt-4.1-nano"  # Using GPT-4 for highest quality medical vignettes


class EnhancedVignetteGenerator:
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

            # Handle different JSON structures
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
        """Enhanced rate limiting to avoid hitting API limits"""
        with self.request_lock:
            self.request_count += 1
            if self.request_count % 50 == 0:  # Every 50 requests
                print(f"🕐 Rate limiting... Processed {self.request_count} requests")
                time.sleep(15)  # 15 second pause for safety
            else:
                time.sleep(0.7)  # Slightly longer delay between requests

    def generate_vignette_with_medical_data(
        self, disease_data: Dict, vignette_number: int, variation_type: str = "typical"
    ) -> str:
        """Generate a vignette using the detailed medical JSON data"""

        disease_name = disease_data.get("disease_name", "Unknown Disease")
        symptoms = disease_data.get("symptoms", [])
        causes = disease_data.get("causes", [])
        risk_factors = disease_data.get("risk_factors", [])

        # Create enhanced prompt using medical data
        prompt = self._create_enhanced_prompt(
            disease_data, vignette_number, variation_type
        )

        try:
            self.rate_limit_delay()

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": """You are a board-certified physician and medical educator specializing in creating realistic, detailed patient vignettes for medical training. Your vignettes should be:
                        - Clinically accurate and based on real medical knowledge
                        - Educationally valuable for diagnostic training
                        - Representative of real-world patient presentations
                        - Varied in complexity and presentation style
                        - Written from the perspective of a patient's actual experience""",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.8,  # Creativity for realistic variation
                max_tokens=1000,  # More space for detailed vignettes
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

    def _create_enhanced_prompt(
        self, disease_data: Dict, vignette_number: int, variation_type: str
    ) -> str:
        """Create an enhanced prompt using the medical JSON data"""

        disease_name = disease_data.get("disease_name", "Unknown Disease")
        symptoms = disease_data.get("symptoms", [])
        causes = disease_data.get("causes", [])
        risk_factors = disease_data.get("risk_factors", [])
        prognosis = disease_data.get("prognosis", "")

        # Select symptoms for this vignette (vary by type)
        if variation_type == "typical":
            primary_symptoms = symptoms[:4] if len(symptoms) >= 4 else symptoms
            secondary_symptoms = symptoms[4:6] if len(symptoms) > 4 else []
        elif variation_type == "atypical":
            # Mix common and uncommon symptoms
            primary_symptoms = symptoms[2:5] if len(symptoms) >= 5 else symptoms[:3]
            secondary_symptoms = (
                symptoms[:2] + symptoms[5:7] if len(symptoms) > 5 else symptoms[3:]
            )
        elif variation_type == "complex":
            # Include more symptoms and complications
            primary_symptoms = symptoms[:5] if len(symptoms) >= 5 else symptoms
            secondary_symptoms = symptoms[5:8] if len(symptoms) > 5 else []
        else:  # minimal
            primary_symptoms = symptoms[:2] if len(symptoms) >= 2 else symptoms
            secondary_symptoms = []

        # Select risk factors
        selected_risk_factors = (
            risk_factors[:3] if len(risk_factors) >= 3 else risk_factors
        )

        # Create demographic variations
        demographics = self._generate_demographics(
            variation_type, selected_risk_factors
        )

        base_prompt = f"""
        Create a detailed, realistic patient vignette for: {disease_name}

        MEDICAL CONTEXT TO INCORPORATE:
        Primary symptoms to include: {', '.join(primary_symptoms)}
        {f"Secondary symptoms (optional): {', '.join(secondary_symptoms)}" if secondary_symptoms else ""}
        Relevant risk factors: {', '.join(selected_risk_factors)}
        {f"Prognosis context: {prognosis[:200]}..." if prognosis else ""}

        PATIENT DEMOGRAPHICS:
        {demographics}

        VIGNETTE REQUIREMENTS:
        - Write as a realistic patient presentation, not a textbook case
        - Include specific age, gender, and relevant demographics  
        - Present symptoms in natural, patient-like language (not medical terminology)
        - Include timeline of symptom development
        - Mention relevant medical history, family history, and social history
        - Include what brought the patient to seek care
        - Show realistic patient concerns and descriptions
        - Length: 200-300 words
        - Make it sound like a real patient encounter

        VARIATION TYPE: {variation_type.upper()}
        """

        # Add variation-specific instructions
        if variation_type == "typical":
            variation_prompt = """
            - Create a classic presentation that would be recognizable to medical students
            - Include the most common symptoms and risk factors
            - Show clear symptom progression
            - Make the diagnosis relatively straightforward
            """
        elif variation_type == "atypical":
            variation_prompt = """
            - Create an unusual or challenging presentation
            - Include unexpected symptoms or demographics
            - Add complexity that might lead to diagnostic uncertainty
            - Show atypical progression or manifestation
            """
        elif variation_type == "complex":
            variation_prompt = """
            - Include multiple comorbidities or complications
            - Show interaction between different medical conditions
            - Include symptoms that could suggest multiple diagnoses
            - Add social or psychological complexity
            """
        else:  # minimal
            variation_prompt = """
            - Create a subtle presentation with minimal symptoms
            - Show early-stage disease or mild manifestation
            - Include vague or nonspecific complaints
            - Demonstrate how patients might initially downplay symptoms
            """

        return (
            f"{base_prompt}\n{variation_prompt}\n\nGenerate the patient vignette now:"
        )

    def _generate_demographics(
        self, variation_type: str, risk_factors: List[str]
    ) -> str:
        """Generate appropriate demographics based on variation type and risk factors"""

        # Age ranges based on variation type
        if variation_type == "typical":
            age_ranges = {
                "young_adult": (25, 40),
                "middle_aged": (45, 65),
                "elderly": (70, 85),
            }
        elif variation_type == "atypical":
            age_ranges = {
                "young": (18, 30),
                "unusual_elderly": (85, 95),
                "unexpected_middle": (35, 50),
            }
        else:
            age_ranges = {"varied": (30, 75)}

        # Select age range
        selected_range = random.choice(list(age_ranges.values()))
        age = random.randint(selected_range[0], selected_range[1])

        # Gender (roughly balanced)
        gender = random.choice(["male", "female"])

        # Occupation variety
        occupations = [
            "teacher",
            "nurse",
            "engineer",
            "retail worker",
            "office manager",
            "construction worker",
            "student",
            "retiree",
            "accountant",
            "chef",
            "social worker",
            "mechanic",
            "sales representative",
            "artist",
        ]
        occupation = random.choice(occupations)

        # Risk factor integration
        risk_context = ""
        if any("smoking" in rf.lower() for rf in risk_factors):
            risk_context += "- History of tobacco use\n"
        if any("age" in rf.lower() or "elderly" in rf.lower() for rf in risk_factors):
            risk_context += f"- Age-related risk factors (patient is {age})\n"
        if any(
            "family" in rf.lower() or "genetic" in rf.lower() for rf in risk_factors
        ):
            risk_context += "- Relevant family history\n"

        return f"""
        Age: {age} years old
        Gender: {gender}
        Occupation: {occupation}
        {risk_context if risk_context else ""}
        """

    def _validate_vignette(self, vignette: str, disease_name: str) -> str:
        """Enhanced validation and cleaning of generated vignette"""
        # Remove unwanted formatting
        vignette = vignette.replace("**", "").replace("##", "").replace("***", "")

        # Remove any meta-commentary about the vignette
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

        # Check length
        if len(vignette) < 150:
            print(f"⚠️ Short vignette for {disease_name} ({len(vignette)} chars)")
        elif len(vignette) > 500:
            print(f"⚠️ Long vignette for {disease_name} ({len(vignette)} chars)")

        return vignette.strip()

    def _create_fallback_vignette(
        self, disease_data: Dict, vignette_number: int
    ) -> str:
        """Create a basic fallback vignette if API call fails"""
        disease_name = disease_data.get("disease_name", "Unknown Disease")
        symptoms = disease_data.get("symptoms", [])

        basic_symptoms = symptoms[:3] if symptoms else ["various symptoms"]

        return f"""A patient presents to the clinic with {', '.join(basic_symptoms[:2])} and {basic_symptoms[2] if len(basic_symptoms) > 2 else 'related symptoms'}. The patient reports that these symptoms have been affecting their daily activities. Further evaluation is needed to establish the diagnosis of {disease_name}. (Fallback vignette {vignette_number} due to generation error)"""


def generate_vignettes_for_disease_with_data(args):
    """Generate multiple vignettes for a single disease using medical data"""
    disease_data, num_vignettes, api_key, model = args
    generator = EnhancedVignetteGenerator(api_key, model)

    disease_name = disease_data.get("disease_name", "Unknown Disease")

    # Define variation types for multiple vignettes
    variation_types = ["typical", "atypical", "complex", "minimal"]

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
    output_file: str = "medical_research_results1.json",
    max_workers: int = 12,
):
    """Generate vignettes from medical JSON data file"""

    # Load medical data
    generator = EnhancedVignetteGenerator(api_key, model)
    medical_data = generator.load_medical_data(medical_json_file)

    if not medical_data:
        print("❌ No medical data loaded. Exiting.")
        return {}

    print(
        f"🏥 Generating {num_vignettes_per_disease} vignettes for {len(medical_data)} diseases"
    )
    print(
        f"📊 Total vignettes to generate: {len(medical_data) * num_vignettes_per_disease}"
    )

    # Prepare arguments for multiprocessing
    args_list = [
        (disease_data, num_vignettes_per_disease, api_key, "gpt-4o")
        for disease_data in medical_data
    ]

    # Generate vignettes
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
                disease_name, vignettes = future.result(
                    timeout=600
                )  # 10 minute timeout
                results[disease_name] = vignettes
                completed += 1

                progress = (completed / len(medical_data)) * 100
                print(
                    f"📈 Progress: {completed}/{len(medical_data)} diseases completed ({progress:.1f}%)"
                )

            except Exception as e:
                disease_name = future_to_disease[future]
                print(f"❌ Failed to generate vignettes for {disease_name}: {e}")
                # Create fallback vignettes
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

    # Save results with enhanced metadata
    output_data = {
        "metadata": {
            "source_file": medical_json_file,
            "total_diseases": len(medical_data),
            "vignettes_per_disease": num_vignettes_per_disease,
            "total_vignettes": len(medical_data) * num_vignettes_per_disease,
            "generation_model": "gpt-4o",
            "variation_types": ["typical", "atypical", "complex", "minimal"],
            "generation_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        },
        "vignettes": results,
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Completed! Enhanced vignettes saved to: {output_file}")

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
    print(f"   Average vignettes per disease: {total_vignettes/len(medical_data):.1f}")

    # Show variation type distribution
    variation_counts = {}
    for disease_vignettes in results.values():
        for vignette_data in disease_vignettes:
            var_type = vignette_data.get("variation_type", "unknown")
            variation_counts[var_type] = variation_counts.get(var_type, 0) + 1

    print(f"\n📋 VARIATION TYPE DISTRIBUTION:")
    for var_type, count in variation_counts.items():
        percentage = (count / total_vignettes) * 100
        print(f"   {var_type}: {count} ({percentage:.1f}%)")

    return results


def validate_enhanced_vignettes(results_file: str):
    """Validate the quality of enhanced generated vignettes"""
    with open(results_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    vignettes_data = data["vignettes"]

    print("\n🔍 ENHANCED VIGNETTE QUALITY VALIDATION:")

    # Quality metrics
    error_count = 0
    short_count = 0
    good_count = 0
    variation_counts = {}

    for disease, disease_vignettes in vignettes_data.items():
        for vignette_data in disease_vignettes:
            vignette = vignette_data.get("vignette", "")
            var_type = vignette_data.get("variation_type", "unknown")

            # Count variation types
            variation_counts[var_type] = variation_counts.get(var_type, 0) + 1

            # Quality assessment
            if "Error" in vignette or "error" in vignette:
                error_count += 1
            elif len(vignette) < 150:
                short_count += 1
            else:
                good_count += 1

    total = error_count + short_count + good_count

    print(f"   ✅ Good quality vignettes: {good_count} ({good_count/total*100:.1f}%)")
    print(f"   ⚠️ Short vignettes: {short_count} ({short_count/total*100:.1f}%)")
    print(f"   ❌ Error vignettes: {error_count} ({error_count/total*100:.1f}%)")

    print(f"\n📊 VARIATION TYPE BREAKDOWN:")
    for var_type, count in variation_counts.items():
        percentage = (count / total) * 100
        print(f"   {var_type}: {count} ({percentage:.1f}%)")

    # Show sample vignettes
    print(f"\n📋 SAMPLE VIGNETTES BY VARIATION TYPE:")
    sample_diseases = list(vignettes_data.keys())[:2]
    for disease in sample_diseases:
        print(f"\n{disease}:")
        for vignette_data in vignettes_data[disease][:2]:  # Show first 2 variations
            var_type = vignette_data.get("variation_type", "unknown")
            vignette = vignette_data.get("vignette", "")
            print(f"   [{var_type.upper()}]: {vignette[:200]}...")


if __name__ == "__main__":
    # Configuration
    API_KEY = "api"
    MEDICAL_JSON_FILE = "/Users/owner/Downloads/coding projects/AMIE-app/medical_research_results.json"  # Your JSON file with disease data
    NUM_VIGNETTES_PER_DISEASE = 4  # Generate 4 variations per disease
    OUTPUT_FILE = "enhanced_medical_vignettes_from_json.json"
    MAX_WORKERS = 12  # Adjust based on your API rate limits

    print("🏥 ENHANCED MEDICAL VIGNETTE GENERATOR WITH JSON DATA")
    print("=" * 60)

    # Check if medical JSON file exists
    if not os.path.exists(MEDICAL_JSON_FILE):
        print(f"❌ Medical JSON file not found: {MEDICAL_JSON_FILE}")
        print(
            "Please ensure your medical disease JSON file is in the current directory."
        )
        exit(1)

    # Generate vignettes using medical JSON data
    results = generate_vignettes_from_medical_json(
        medical_json_file=MEDICAL_JSON_FILE,
        api_key=API_KEY,
        num_vignettes_per_disease=NUM_VIGNETTES_PER_DISEASE,
        output_file=OUTPUT_FILE,
        max_workers=MAX_WORKERS,
    )

    # Validate results
    validate_enhanced_vignettes(OUTPUT_FILE)

    print(
        f"\n🚀 Ready for training! Use {OUTPUT_FILE} as input for your conversation generation pipeline."
    )
    print(
        f"📁 Make sure to also keep {MEDICAL_JSON_FILE} for the adaptive hinting system!"
    )

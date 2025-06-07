import os
import json
import time
import random
from openai import OpenAI
from typing import Dict, List, Any, Optional
import multiprocessing
from concurrent.futures import ThreadPoolExecutor, as_completed
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
                time.sleep(0.1)

    def generate_single_vignette(
        self, disease_data: Dict, vignette_number: int
    ) -> Dict:
        """Generate a single roleplay script for an AI agent to act as the patient"""

        disease_name = disease_data.get("disease_name", "Unknown Disease")

        try:
            # Create roleplay script prompt
            prompt = self._create_roleplay_script_prompt(disease_data, vignette_number)

            self.rate_limit_delay()

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": """You are a medical training specialist creating ROLEPLAY SCRIPTS for AI agents to act as patients. 

Your job is to create CHARACTER BRIEFS that tell an AI agent exactly how to roleplay a patient with a specific medical condition.

CRITICAL REQUIREMENTS:
- Write AS the patient character, not ABOUT them
- Create acting instructions for the AI agent
- Include specific dialogue, behaviors, and emotional responses
- Make it medically accurate while being realistic for the character
- Provide clear roleplay directions
- Focus on how the character would naturally speak and act""",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=800,
            )

            vignette = response.choices[0].message.content.strip()
            validated_vignette = self._validate_vignette(vignette, disease_name)

            print(f"✅ Generated script {vignette_number} for {disease_name}")

            print(f"Vignette content:\n{validated_vignette}\n")

            return {
                "roleplay_script": validated_vignette,
                "variation_type": "typical",
                "script_number": vignette_number,
                "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "disease_name": disease_name,
                "success": True,
            }

        except Exception as e:
            print(
                f"❌ Error generating script {vignette_number} for {disease_name}: {str(e)}"
            )

            return {
                "roleplay_script": self._create_fallback_vignette(
                    disease_data, vignette_number
                ),
                "variation_type": "typical",
                "script_number": vignette_number,
                "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "error": str(e),
                "disease_name": disease_name,
                "success": False,
            }

    def _create_roleplay_script_prompt(
        self, disease_data: Dict, vignette_number: int
    ) -> str:
        """Create a prompt for generating roleplay scripts for AI agents - TYPICAL presentation only"""

        disease_name = disease_data.get("disease_name", "Unknown Disease")
        symptoms = disease_data.get("symptoms", [])
        causes = disease_data.get("causes", [])
        risk_factors = disease_data.get("risk_factors", [])
        prognosis = disease_data.get("prognosis", "")

        # Use typical symptom selection (first 5 symptoms for classic presentation)
        selected_symptoms = symptoms[:5] if len(symptoms) >= 5 else symptoms

        # Medical accuracy instructions
        medical_accuracy_note = self._get_medical_accuracy_instructions(
            disease_name, risk_factors
        )

        base_prompt = f"""
        Create a ROLEPLAY SCRIPT for an AI agent to act as a patient with: {disease_name}

        MEDICAL DATA TO INCORPORATE:
        Primary symptoms: {', '.join(selected_symptoms)}
        Risk factors: {', '.join(risk_factors[:4])}
        Underlying causes: {', '.join(causes[:3])}
        {f"Clinical context: {prognosis[:150]}..." if prognosis else ""}

        DEMOGRAPHIC REQUIREMENTS:
        {medical_accuracy_note}

        FORMAT YOUR RESPONSE AS A ROLEPLAY SCRIPT:

        **PATIENT CHARACTER:** [Name, age, brief background]
        **SCENARIO:** {disease_name} - typical presentation

        **CHARACTER BACKGROUND:**
        - [Occupation/school/life situation]
        - [Family situation]
        - [Relevant medical/social history]

        **CURRENT MEDICAL SITUATION:**
        - [Current symptoms in patient's own words]
        - [Timeline of symptom development]
        - [Pain/discomfort levels]
        - [What prompted today's visit]

        **ROLEPLAY INSTRUCTIONS:**
        You are a patient seeking medical care for concerning symptoms. Your symptoms are typical for this condition.

        Make your vignette in paragraph form, and make it realistic. 

        """

        return base_prompt

    def _generate_patient_names(
        self, disease_name: str, risk_factors: List[str]
    ) -> List[str]:
        """Generate appropriate patient names based on demographics"""

        # Default names by age/gender patterns
        adult_female_names = [
            "Sarah",
            "Jennifer",
            "Lisa",
            "Maria",
            "Ashley",
            "Jessica",
            "Amanda",
            "Michelle",
        ]
        adult_male_names = [
            "Michael",
            "David",
            "James",
            "Robert",
            "John",
            "Christopher",
            "Matthew",
            "Daniel",
        ]
        elderly_female_names = [
            "Dorothy",
            "Helen",
            "Margaret",
            "Ruth",
            "Betty",
            "Patricia",
            "Barbara",
            "Joan",
        ]
        elderly_male_names = [
            "Robert",
            "William",
            "Richard",
            "Charles",
            "George",
            "Frank",
            "Edward",
            "Harold",
        ]
        child_names = [
            "Emma",
            "Sophia",
            "Liam",
            "Noah",
            "Olivia",
            "Ava",
            "Mason",
            "Lucas",
            "Isabella",
            "Ethan",
        ]

        # Gender-specific conditions
        if any(
            term in disease_name.lower()
            for term in ["pregnancy", "maternal", "ovarian", "cervical", "uterine"]
        ):
            return adult_female_names
        elif any(term in disease_name.lower() for term in ["prostate", "testicular"]):
            return adult_male_names
        elif any(
            term in disease_name.lower()
            for term in ["pediatric", "childhood", "neonatal"]
        ):
            return child_names
        elif any(
            term in disease_name.lower()
            for term in ["elderly", "geriatric", "age-related"]
        ):
            return elderly_female_names + elderly_male_names

        # Default to mixed adult names
        return adult_female_names + adult_male_names

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
        """Clean and validate the generated roleplay script"""
        # Remove excessive formatting
        vignette = vignette.replace("***", "").replace("###", "")

        # Remove any meta-commentary that breaks roleplay
        lines = vignette.split("\n")
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            if line and not any(
                phrase in line.lower()
                for phrase in [
                    "this script",
                    "this roleplay",
                    "note to trainer:",
                    "training note:",
                ]
            ):
                cleaned_lines.append(line)

        vignette = "\n".join(cleaned_lines)

        # Ensure it starts appropriately for a roleplay script
        if not any(
            vignette.startswith(prefix)
            for prefix in [
                "**PATIENT CHARACTER:**",
                "PATIENT CHARACTER:",
                "**CHARACTER:**",
                "CHARACTER:",
            ]
        ):
            vignette = (
                f"**PATIENT CHARACTER:** Patient with {disease_name}\n\n{vignette}"
            )

        return vignette.strip()

    def _create_fallback_vignette(
        self, disease_data: Dict, vignette_number: int
    ) -> str:
        """Create a basic fallback roleplay script if API call fails"""
        disease_name = disease_data.get("disease_name", "Unknown Disease")
        symptoms = disease_data.get("symptoms", [])

        basic_symptoms = symptoms[:3] if symptoms else ["various symptoms"]

        return f"""**PATIENT CHARACTER:** Patient, age 35, with {disease_name}

**SCENARIO:** {disease_name} - Typical presentation

**ROLEPLAY INSTRUCTIONS:**
You are a patient seeking medical care for concerning symptoms.

SYMPTOMS TO DESCRIBE:
- {basic_symptoms[0] if len(basic_symptoms) > 0 else "concerning symptoms"}
- {basic_symptoms[1] if len(basic_symptoms) > 1 else "related discomfort"}
- {basic_symptoms[2] if len(basic_symptoms) > 2 else "additional symptoms"}

MAIN CONCERNS:
- "What could be causing this?"
- "Is this something serious?"
- "What should I do about it?"

(Fallback roleplay script {vignette_number})"""


def save_current_progress(
    results: Dict,
    medical_data: List[Dict],
    num_vignettes_per_disease: int,
    medical_json_file: str,
    output_file: str,
    model: str,
):
    """Save current progress to JSON file with enhanced error handling"""
    try:
        current_time = time.strftime("%Y-%m-%d %H:%M:%S")

        output_data = {
            "metadata": {
                "source_file": medical_json_file,
                "total_diseases": len(medical_data),
                "scripts_per_disease": num_vignettes_per_disease,
                "total_scripts": len(medical_data) * num_vignettes_per_disease,
                "completed_diseases": len(results),
                "generation_model": model,
                "variation_types": ["typical"],
                "generation_timestamp": current_time,
                "last_update": current_time,
                "focus": "roleplay_scripts_for_ai_agents",
                "format": "patient_character_briefs",
                "presentation_type": "typical_only",
                "status": (
                    "in_progress" if len(results) < len(medical_data) else "completed"
                ),
            },
            "roleplay_scripts": results,
        }

        # Create backup filename
        backup_file = f"backup_{output_file}"

        # Write to backup first
        with open(backup_file, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        # If backup successful, write to main file
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        # Print file size for confirmation
        file_size = os.path.getsize(output_file) / 1024  # KB
        print(
            f"💾 SAVED: {output_file} ({file_size:.1f} KB) - {len(results)} diseases completed at {current_time}"
        )

        # Remove backup after successful save
        if os.path.exists(backup_file):
            os.remove(backup_file)

    except Exception as e:
        print(f"❌ ERROR SAVING FILE: {e}")
        print(f"   Attempted to save {len(results)} completed diseases")
        print(f"   Check disk space and file permissions")


def generate_single_vignette_wrapper(args):
    """Wrapper function for generating a single vignette (needed for multiprocessing)"""
    disease_data, vignette_number, api_key, model_name = args
    generator = MedicallyAccurateVignetteGenerator(api_key, model_name)
    return generator.generate_single_vignette(disease_data, vignette_number)


def generate_vignettes_from_medical_json(
    medical_json_file: str,
    api_key: str,
    num_vignettes_per_disease: int = 2,
    output_file: str = "patient_roleplay_scripts_typical.json",
    max_workers: int = 12,
):
    """Generate TYPICAL roleplay scripts with TRUE parallel processing"""

    generator = MedicallyAccurateVignetteGenerator(api_key, model)
    medical_data = generator.load_medical_data(medical_json_file)

    if not medical_data:
        print("❌ No medical data loaded. Exiting.")
        return {}

    print(
        f"🎭 Generating {num_vignettes_per_disease} TYPICAL ROLEPLAY SCRIPTS for {len(medical_data)} diseases"
    )
    print(
        f"📊 Total scripts to generate: {len(medical_data) * num_vignettes_per_disease}"
    )
    print(f"⚡ Using {max_workers} parallel workers (ACTUAL THREADING)")
    print(f"💾 Progress will be saved every 10 completed vignettes to: {output_file}")

    # Create ALL individual vignette tasks (this is the key to true parallelism)
    all_tasks = []
    for disease_data in medical_data:
        for vignette_num in range(1, num_vignettes_per_disease + 1):
            all_tasks.append((disease_data, vignette_num, api_key, model))

    print(
        f"🔥 Created {len(all_tasks)} individual vignette tasks for parallel processing"
    )

    results = {}
    completed_vignettes = 0
    save_lock = threading.Lock()

    # Create initial file
    print(f"\n📁 Creating initial empty file...")
    save_current_progress(
        results,
        medical_data,
        num_vignettes_per_disease,
        medical_json_file,
        output_file,
        model,
    )

    # === TRUE PARALLEL PROCESSING OF INDIVIDUAL VIGNETTES ===
    print(f"\n🚀 Starting parallel processing with {max_workers} workers...")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit ALL individual vignette tasks
        future_to_task = {
            executor.submit(generate_single_vignette_wrapper, task): task
            for task in all_tasks
        }

        print(f"📤 Submitted {len(future_to_task)} tasks to thread pool")

        # Process completed vignettes as they finish
        for future in as_completed(future_to_task):
            task = future_to_task[future]
            disease_data, vignette_num, _, _ = task
            disease_name = disease_data.get("disease_name", "Unknown Disease")

            try:
                vignette_result = future.result()

                with save_lock:
                    # Initialize disease entry if not exists
                    if disease_name not in results:
                        results[disease_name] = []

                    # Add this vignette to the disease
                    results[disease_name].append(
                        {
                            "roleplay_script": vignette_result["roleplay_script"],
                            "variation_type": vignette_result["variation_type"],
                            "script_number": vignette_result["script_number"],
                            "generated_at": vignette_result["generated_at"],
                        }
                    )

                    completed_vignettes += 1

                    # Save every 10 vignettes
                    if completed_vignettes % 10 == 0 or completed_vignettes == len(
                        all_tasks
                    ):
                        save_current_progress(
                            results,
                            medical_data,
                            num_vignettes_per_disease,
                            medical_json_file,
                            output_file,
                            model,
                        )

                progress = (completed_vignettes / len(all_tasks)) * 100
                disease_progress = len(results)
                print(
                    f"✅ Completed vignette {vignette_num} for {disease_name} - Progress: {completed_vignettes}/{len(all_tasks)} ({progress:.1f}%) - {disease_progress} diseases started"
                )
                

            except Exception as e:
                print(f"❌ Failed vignette {vignette_num} for {disease_name}: {e}")

                with save_lock:
                    # Add fallback entry
                    if disease_name not in results:
                        results[disease_name] = []

                    results[disease_name].append(
                        {
                            "roleplay_script": f"Error generating roleplay script for {disease_name} (script {vignette_num})",
                            "variation_type": "typical",
                            "script_number": vignette_num,
                            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                            "error": str(e),
                        }
                    )

                    completed_vignettes += 1

    # Final save
    print(f"\n🏁 Doing final save...")
    save_current_progress(
        results,
        medical_data,
        num_vignettes_per_disease,
        medical_json_file,
        output_file,
        model,
    )

    print(f"\n✅ Completed! Typical roleplay scripts saved to: {output_file}")

    # Summary statistics
    total_scripts = sum(len(vignettes) for vignettes in results.values())
    successful_diseases = sum(
        1
        for vignettes in results.values()
        if not any("Error" in v.get("roleplay_script", "") for v in vignettes)
    )

    print(f"\n📊 GENERATION SUMMARY:")
    print(f"   Total diseases processed: {len(results)}")
    print(f"   Successful diseases: {successful_diseases}")
    print(f"   Total scripts generated: {total_scripts}")
    print(f"   Workers used: {max_workers}")
    print(f"   Format: Character briefs for AI agent roleplay")
    print(f"   🔥 ACTUAL PARALLEL PROCESSING ACHIEVED!")

    return results


if __name__ == "__main__":
    # Configuration
    API_KEY = "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"
    MEDICAL_JSON_FILE = "combined.json"
    NUM_VIGNETTES_PER_DISEASE = 1
    OUTPUT_FILE = "patient_roleplay_scripts_typical.json"
    MAX_WORKERS = 1  # NOW ACTUALLY USED FOR REAL PARALLEL PROCESSING!

    print("🎭 PATIENT ROLEPLAY SCRIPT GENERATOR - WITH REAL PARALLEL PROCESSING")
    print("=" * 70)
    print(f"🔥 Using {MAX_WORKERS} workers to process individual vignettes in parallel")
    print("💾 Progress saved every 10 completed vignettes")

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

    print(
        f"\n🚀 Ready for AI agent training! Typical roleplay scripts in: {OUTPUT_FILE}"
    )

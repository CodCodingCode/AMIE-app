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
                time.sleep(0.1)

    def generate_vignette_with_medical_data(
        self, disease_data: Dict, vignette_number: int, variation_type: str = "typical"
    ) -> str:
        """Generate a roleplay script for an AI agent to act as the patient"""

        disease_name = disease_data.get("disease_name", "Unknown Disease")

        # Create roleplay script prompt
        prompt = self._create_roleplay_script_prompt(
            disease_data, vignette_number, variation_type
        )

        try:
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

            print(
                f"✅ Generated {variation_type} roleplay script {vignette_number} for {disease_name}"
            )
            return validated_vignette

        except Exception as e:
            print(f"❌ Error generating roleplay script for {disease_name}: {str(e)}")
            return self._create_fallback_vignette(disease_data, vignette_number)

    def _create_roleplay_script_prompt(
        self, disease_data: Dict, vignette_number: int, variation_type: str
    ) -> str:
        """Create a prompt for generating roleplay scripts for AI agents"""

        disease_name = disease_data.get("disease_name", "Unknown Disease")
        symptoms = disease_data.get("symptoms", [])
        causes = disease_data.get("causes", [])
        risk_factors = disease_data.get("risk_factors", [])
        prognosis = disease_data.get("prognosis", "")

        # Select different symptom combinations for variation
        if variation_type == "typical":
            selected_symptoms = symptoms[:5] if len(symptoms) >= 5 else symptoms
        elif variation_type == "early":
            selected_symptoms = symptoms[:3] if len(symptoms) >= 3 else symptoms
        elif variation_type == "severe":
            selected_symptoms = symptoms[:7] if len(symptoms) >= 7 else symptoms
        else:  # mixed
            if len(symptoms) >= 6:
                selected_symptoms = symptoms[:2] + symptoms[3:6]
            else:
                selected_symptoms = symptoms

        # Medical accuracy instructions
        medical_accuracy_note = self._get_medical_accuracy_instructions(
            disease_name, risk_factors
        )

        # Generate random but appropriate name
        patient_names = self._generate_patient_names(disease_name, risk_factors)

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
        **SCENARIO:** {disease_name} - {variation_type} presentation

        **CHARACTER BACKGROUND:**
        - [Occupation/school/life situation]
        - [Family situation]
        - [Personality traits]
        - [Relevant medical/social history]

        **CURRENT MEDICAL SITUATION:**
        - [Current symptoms in patient's own words]
        - [Timeline of symptom development]
        - [Pain/discomfort levels]
        - [What prompted today's visit]

        **ROLEPLAY INSTRUCTIONS:**
        You are [character name]. Act exactly like this character would.

        OPENING STATEMENT: "[First thing the patient would say to the doctor]"

        PERSONALITY TO EXHIBIT:
        - [Key personality traits]
        - [Emotional state]
        - [Communication style]

        KEY PHRASES TO USE:
        - [Specific ways they describe their symptoms]
        - [Questions they would ask]
        - [Concerns they would express]

        BEHAVIORS TO SHOW:
        - [Physical actions/gestures]
        - [Body language]
        - [Non-verbal cues]

        INFORMATION FLOW:
        VOLUNTEER IMMEDIATELY:
        - [What they'll share first]
        
        SHARE ONLY IF ASKED:
        - [Information requiring prompting]
        
        MAIN CONCERNS:
        - [Their biggest fears/worries]
        - [What they hope to achieve]

        VARIATION TYPE: {variation_type.upper()}
        """

        # Add variation-specific roleplay instructions
        if variation_type == "typical":
            variation_instructions = """
            ROLEPLAY FOCUS:
            - Act as a classic presentation of this condition
            - Show clear, recognizable symptoms
            - Be cooperative and forthcoming with information
            - Display appropriate concern for a typical case
            """
        elif variation_type == "early":
            variation_instructions = """
            ROLEPLAY FOCUS:
            - Act uncertain about seeking medical care
            - Minimize symptoms initially ("maybe it's nothing")
            - Be hesitant to "waste the doctor's time"
            - Show mild symptoms that are just starting to worry you
            """
        elif variation_type == "severe":
            variation_instructions = """
            ROLEPLAY FOCUS:
            - Show distress and urgency
            - Indicate symptoms have significantly worsened
            - Express fear about serious complications
            - May have delayed seeking care until symptoms became severe
            """
        else:  # mixed
            variation_instructions = """
            ROLEPLAY FOCUS:
            - Present with some unusual or atypical features
            - Show varying symptom severity
            - Be somewhat confused about your symptoms
            - Include both early and more developed symptoms
            """

        return f"{base_prompt}\n{variation_instructions}\n\nGenerate the complete roleplay script for the AI agent:"

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

**SCENARIO:** {disease_name} - Standard presentation

**ROLEPLAY INSTRUCTIONS:**
You are a patient seeking medical care for concerning symptoms.

OPENING STATEMENT: "Doctor, I've been having some health issues that are worrying me."

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
                "variation_types": ["typical", "early", "severe", "mixed"],
                "generation_timestamp": current_time,
                "last_update": current_time,
                "focus": "roleplay_scripts_for_ai_agents",
                "format": "patient_character_briefs",
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


def generate_vignettes_for_disease_with_data(args):
    """Generate multiple roleplay scripts for a single disease"""
    disease_data, num_vignettes, api_key, model = args
    generator = MedicallyAccurateVignetteGenerator(api_key, model)

    disease_name = disease_data.get("disease_name", "Unknown Disease")

    # Variation types focused on medical presentation
    variation_types = ["typical", "early", "severe", "mixed"]

    vignettes = []
    for i in range(num_vignettes):
        try:
            variation_type = variation_types[i % len(variation_types)]

            print(
                f"🔄 Generating {variation_type} script {i+1}/{num_vignettes} for: {disease_name}"
            )

            vignette = generator.generate_vignette_with_medical_data(
                disease_data, i + 1, variation_type
            )
            vignettes.append(
                {
                    "roleplay_script": vignette,
                    "variation_type": variation_type,
                    "script_number": i + 1,
                    "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                }
            )

            print(f"✅ Completed {variation_type} script {i+1} for: {disease_name}")

        except Exception as e:
            print(
                f"❌ Failed to generate roleplay script {i+1} for {disease_name}: {e}"
            )
            vignettes.append(
                {
                    "roleplay_script": generator._create_fallback_vignette(
                        disease_data, i + 1
                    ),
                    "variation_type": "fallback",
                    "script_number": i + 1,
                    "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "error": str(e),
                }
            )

    return disease_name, vignettes


def generate_vignettes_from_medical_json(
    medical_json_file: str,
    api_key: str,
    num_vignettes_per_disease: int = 2,
    output_file: str = "patient_roleplay_scripts.json",
    max_workers: int = 12,
):
    """Generate roleplay scripts for AI agents from medical JSON data with enhanced incremental saving"""

    generator = MedicallyAccurateVignetteGenerator(api_key, model)
    medical_data = generator.load_medical_data(medical_json_file)

    if not medical_data:
        print("❌ No medical data loaded. Exiting.")
        return {}

    print(
        f"🎭 Generating {num_vignettes_per_disease} ROLEPLAY SCRIPTS for {len(medical_data)} diseases"
    )
    print(
        f"📊 Total scripts to generate: {len(medical_data) * num_vignettes_per_disease}"
    )
    print(f"💾 Progress will be saved IMMEDIATELY after each disease to: {output_file}")
    print(f"⚡ You can monitor progress by checking the file size and content!")

    args_list = [
        (disease_data, num_vignettes_per_disease, api_key, model)
        for disease_data in medical_data
    ]

    results = {}
    completed = 0
    save_lock = threading.Lock()  # Thread safety for saving

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

    # Process diseases sequentially to ensure immediate saving
    for i, args in enumerate(args_list):
        disease_data = args[0]
        disease_name = disease_data.get("disease_name", f"Disease_{i}")

        print(f"\n🏥 Starting disease {i+1}/{len(args_list)}: {disease_name}")

        try:
            # Generate vignettes for this disease
            disease_name, vignettes = generate_vignettes_for_disease_with_data(args)

            # IMMEDIATELY save after each disease
            with save_lock:
                results[disease_name] = vignettes
                completed += 1

                # Save progress RIGHT NOW
                save_current_progress(
                    results,
                    medical_data,
                    num_vignettes_per_disease,
                    medical_json_file,
                    output_file,
                    model,
                )

            progress = (completed / len(medical_data)) * 100
            print(
                f"📈 Progress: {completed}/{len(medical_data)} diseases completed ({progress:.1f}%)"
            )
            print(f"💾 File updated with {len(vignettes)} new scripts!")

        except Exception as e:
            print(f"❌ Failed to generate roleplay scripts for {disease_name}: {e}")

            # Save fallback immediately
            with save_lock:
                fallback_vignettes = []
                for j in range(num_vignettes_per_disease):
                    fallback_vignettes.append(
                        {
                            "roleplay_script": f"Error generating roleplay script for {disease_name} (script {j+1})",
                            "variation_type": "error",
                            "script_number": j + 1,
                            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                            "error": str(e),
                        }
                    )
                results[disease_name] = fallback_vignettes
                completed += 1

                # Save even failed attempts immediately
                save_current_progress(
                    results,
                    medical_data,
                    num_vignettes_per_disease,
                    medical_json_file,
                    output_file,
                    model,
                )

    # Final save with completed status
    print(f"\n🏁 Doing final save...")
    save_current_progress(
        results,
        medical_data,
        num_vignettes_per_disease,
        medical_json_file,
        output_file,
        model,
    )

    print(f"\n✅ Completed! Roleplay scripts saved to: {output_file}")

    # Summary statistics
    total_scripts = sum(len(vignettes) for vignettes in results.values())
    successful_diseases = sum(
        1
        for vignettes in results.values()
        if not any("Error" in v.get("roleplay_script", "") for v in vignettes)
    )

    print(f"\n📊 GENERATION SUMMARY:")
    print(f"   Total diseases processed: {len(medical_data)}")
    print(f"   Successful diseases: {successful_diseases}")
    print(f"   Total roleplay scripts generated: {total_scripts}")
    print(f"   Format: Character briefs for AI agent roleplay")
    print(f"   💾 File saved after EVERY single disease completion!")

    return results


if __name__ == "__main__":
    # Configuration
    API_KEY = "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"
    MEDICAL_JSON_FILE = "combined.json"
    NUM_VIGNETTES_PER_DISEASE = 4
    OUTPUT_FILE = "patient_roleplay_scripts.json"
    MAX_WORKERS = 12  # Sequential processing for immediate saving

    print("🎭 PATIENT ROLEPLAY SCRIPT GENERATOR")
    print("=" * 50)
    print("🎯 Creating character briefs for AI agents to roleplay patients")
    print("💾 WITH IMMEDIATE SAVING - File updates after EVERY disease!")

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

    print(f"\n🚀 Ready for AI agent training! Roleplay scripts in: {OUTPUT_FILE}")

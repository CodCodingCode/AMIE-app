import requests
import json

# ============================================================================
# REPLACE THESE WITH YOUR ACTUAL VALUES
# ============================================================================
ENDPOINT_URL = "https://glg6vtpv72vt2jad.us-east-1.aws.endpoints.huggingface.cloud"  # Your endpoint URL from the screenshot
HF_TOKEN = "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"  # Your HuggingFace token


class HuggingFaceInference:
    def __init__(self, endpoint_url, api_token):
        self.endpoint_url = endpoint_url
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
        }

    def generate(self, prompt, max_new_tokens=1000):
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": max_new_tokens,
                "temperature": 0.7,
                "do_sample": True,
                "return_full_text": True,
            },
        }

        try:
            response = requests.post(
                self.endpoint_url, headers=self.headers, json=payload
            )
            response.raise_for_status()

            result = response.json()

            # Handle the response format
            if isinstance(result, list) and len(result) > 0:
                generated_text = result[0].get("generated_text", "")
            else:
                generated_text = str(result)

            return generated_text

        except requests.exceptions.RequestException as e:
            print(f"❌ API request failed: {e}")
            if hasattr(e, "response") and e.response is not None:
                print(f"Status: {e.response.status_code}")
                print(f"Response: {e.response.text}")
            raise


# Initialize the inference client
model_client = HuggingFaceInference(ENDPOINT_URL, HF_TOKEN)


# Test the connection first
def test_connection():
    try:
        print("🔄 Testing endpoint connection...")
        result = model_client.generate("Hello, this is a test.", max_new_tokens=20)
        print(f"✅ Connection successful!")
        print(f"📝 Test result: {result[:100]}...")
        return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False


# Your original conversation logic - now using the endpoint
def run_conversation():
    # Test connection first
    if not test_connection():
        print("Please check your ENDPOINT_URL and HF_TOKEN")
        return

    print("\n" + "=" * 60)
    print("🏥 Starting Clinical Conversation")
    print("=" * 60)

    convo = []
    prev_questions = []
    convo.append("Doctor: What brings you in today?")
    patient_response = "I am 17. I am a female. I have had this really bad headache since yesterday that won't go away. It's on the left side of my head and feels like throbbing. Light hurts my eyes and loud noises make it worse. I threw up once this morning. My mom gets migraines too."
    convo.append(f"Patient: {patient_response}")
    prev_vignette = ""

    for i in range(10):
        print(f"\n{'='*20} Iteration {i+1} {'='*20}")

        # 1. Clinical Summary Generation
        input_text = f"""
Instruction: You are a clinical summarizer. Given a transcript of a doctor–patient dialogue, extract a structured clinical vignette summarizing the key symptoms, relevant history, and any diagnostic clues.
Input: {patient_response} Previous Vignette: {prev_vignette}
Output: THINKING: 
"""

        print("🔄 Generating clinical summary...")
        raw_output = model_client.generate(input_text, max_new_tokens=1000)
        output = (
            raw_output.split("ANSWER:")[-1].strip()
            if "ANSWER:" in raw_output
            else raw_output
        )
        print("📋 Clinical Summary Output:")
        print(raw_output)
        print("\n" + "-" * 50)

        # 2. Diagnostic Reasoning
        input_text2 = f"""
Instruction: You are a diagnostic reasoning model (Early Stage). Based on the patient vignette and early-stage observations, generate a list of plausible diagnoses with reasoning. Focus on broad differentials, considering common and uncommon conditions
Input: {output}
Output: THINKING:
"""

        print("🔄 Generating diagnostic reasoning...")
        raw_output = model_client.generate(input_text2, max_new_tokens=1000)
        output2 = (
            raw_output.split("ANSWER:")[-1].strip()
            if "ANSWER:" in raw_output
            else raw_output
        )
        print("🩺 Diagnostic Reasoning Output:")
        print(raw_output)
        print("\n" + "-" * 50)

        # 3. Question Generation
        input_text3 = f"""
Instruction: You are a questioning agent (Early Stage). Your task is to propose highly relevant early-stage questions that can open the differential diagnosis widely. Use epidemiology, demographics, and vague presenting symptoms as guides.
Input: VIGNETTE: {output} DIAGNOSIS: {output2} PREVIOUS Questions: {prev_questions} Conversation History: {convo}
Output: THINKING:
"""

        print("🔄 Generating next question...")
        raw_output = model_client.generate(input_text3, max_new_tokens=1000)

        if i == 5:
            print("🏁 Reached iteration limit (5). Final diagnosis:")
            print(output2)
            break

        doctor_output = (
            raw_output.split("ANSWER:")[-1].strip()
            if "ANSWER:" in raw_output
            else raw_output
        )
        print("❓ Question Generation Output:")
        print(raw_output)
        print("\n" + "-" * 50)

        print(f"\n🩺 Doctor: {doctor_output}")
        convo.append(f"Doctor: {doctor_output}")
        prev_questions.append(doctor_output)

        input_text4 = f"""
Instruction: You are a board-certified clinician. Based on the provided diagnosis and patient vignette, propose a realistic, evidence-based treatment plan suitable for initiation by a primary care physician or psychiatrist.
Input: Diagnosis: {output2} Vignette: {output}
Output: THINKING:
"""
        raw_output = model_client.generate(input_text4, max_new_tokens=1000)
        output = (
            raw_output.split("ANSWER:")[-1].strip()
            if "ANSWER:" in raw_output
            else raw_output
        )
        print("💊 Treatment Plan Output:" raw_output)

        patient_response = str(input("👤 Patient Response: "))
        convo.append(f"Patient: {patient_response}")
        prev_vignette = output

    print("\n✅ Conversation finished!")


# Optional: Test just one generation
def test_single_generation():
    test_prompt = """
Instruction: You are a clinical summarizer. Given a transcript of a doctor–patient dialogue, extract a structured clinical vignette summarizing the key symptoms, relevant history, and any diagnostic clues.
Input: I am 14. I am a male. I have pain in my stomach. Previous Vignette: 
Output: THINKING: 
"""

    print("🧪 Testing single generation...")
    result = model_client.generate(test_prompt, max_new_tokens=200)
    print("📝 Result:")
    print(result)


if __name__ == "__main__":
    print("🚀 Clinical AI with HuggingFace Inference Endpoint")
    print(f"🔗 Endpoint: {ENDPOINT_URL}")
    print(f"🔑 Token: {HF_TOKEN[:8]}..." if HF_TOKEN else "❌ No token provided")

    # Uncomment the line below to test a single generation first
    # test_single_generation()

    # Run the full conversation
    run_conversation()


files = {
    "You are a clinical summarizer. Given a transcript of a doctor–patient dialogue, extract a structured clinical vignette summarizing the key symptoms, relevant history, and any diagnostic clues.": "all_summarizer_outputs.json",
    "You are a behavioral identifying agent. Based on the provided patient responses, please identify and list the key behavioral indicators that could suggest a specific diagnosis.": "all_behavioral_analyses.json",
    "You are a board-certified clinician. Based on the provided diagnosis and patient vignette, propose a realistic, evidence-based treatment plan suitable for initiation by a primary care physician or psychiatrist.": "all_treatment_outputs.json",
    "You are a diagnostic reasoning model (Early Stage). Based on the patient vignette and early-stage observations, generate a list of plausible diagnoses with reasoning. Focus on broad differentials, considering common and uncommon conditions.": "ED.json",
    "You are a diagnostic reasoning model (Middle Stage). Given the current vignette, prior dialogue, and diagnostic hypothesis, refine the list of possible diagnoses with concise justifications for each. Aim to reduce diagnostic uncertainty.": "MD.json",
    "You are a diagnostic reasoning model (Late Stage). Based on the final patient vignette summary and full conversation, provide the most likely diagnosis with structured reasoning. Confirm diagnostic certainty and include END if no more questioning is necessary.": "LD.json",
    "You are a questioning agent (Early Stage). Your task is to propose highly relevant early-stage questions that can open the differential diagnosis widely. Use epidemiology, demographics, and vague presenting symptoms as guides.": "E.json",
    "You are a questioning agent (Middle Stage). Using the current diagnosis, past questions, and patient vignette, generate a specific question to refine the current differential diagnosis. Return your reasoning and next question.": "M.json",
    "You are a questioning agent (Late Stage). Based on narrowed differentials and previous dialogue, generate a focused question that would help confirm or eliminate the final 1-2 suspected diagnoses.": "L.json",
}

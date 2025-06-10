import requests
import json
import os
from datetime import datetime

# ============================================================================
# REPLACE THESE WITH YOUR ACTUAL VALUES
# ============================================================================
ENDPOINT_URL = "cloudurl"  # Your endpoint URL from the screenshot
HF_TOKEN = "huggingface"  # Your HuggingFace token

class HuggingFaceInference:
    def __init__(self, endpoint_url, api_token):
        self.endpoint_url = endpoint_url
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
        }

    def generate(self, prompt, max_new_tokens=400):
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


class MultiStageClinicianAI:
    def __init__(self, model_client):
        self.model_client = model_client
        self.stage_thresholds = {
            'early': (0, 3),    # Iterations 0-3
            'middle': (4, 7),   # Iterations 4-7
            'late': (8, 12)     # Iterations 8-12
        }
        
        # Storage for all outputs
        self.all_outputs = {
            'summarizer': [],
            'behavioral': [],
            'treatment': [],
            'early_diagnostic': [],
            'middle_diagnostic': [],
            'late_diagnostic': [],
            'early_questions': [],
            'middle_questions': [],
            'late_questions': []
        }
        
        # Prompts dictionary
        self.prompts = {
            'summarizer': "You are a clinical summarizer. Given a transcript of a doctor–patient dialogue, extract a structured clinical vignette summarizing the key symptoms, relevant history, and any diagnostic clues.",
            'behavioral': "You are a behavioral identifying agent. Based on the provided patient responses, please identify and list the key behavioral indicators that could suggest a specific diagnosis.",
            'treatment': "You are a board-certified clinician. Based on the provided diagnosis and patient vignette, propose a realistic, evidence-based treatment plan suitable for initiation by a primary care physician or psychiatrist.",
            'early_diagnostic': "You are a diagnostic reasoning model (Early Stage). Based on the patient vignette and early-stage observations, generate a list of plausible diagnoses with reasoning. Focus on broad differentials, considering common and uncommon conditions.",
            'middle_diagnostic': "You are a diagnostic reasoning model (Middle Stage). Given the current vignette, prior dialogue, and diagnostic hypothesis, refine the list of possible diagnoses with concise justifications for each. Aim to reduce diagnostic uncertainty.",
            'late_diagnostic': "You are a diagnostic reasoning model (Late Stage). Based on the final patient vignette summary and full conversation, provide the most likely diagnosis with structured reasoning. Confirm diagnostic certainty and include END if no more questioning is necessary.",
            'early_questions': "You are a questioning agent (Early Stage). Your task is to propose highly relevant early-stage questions that can open the differential diagnosis widely. Use epidemiology, demographics, and vague presenting symptoms as guides.",
            'middle_questions': "You are a questioning agent (Middle Stage). Using the current diagnosis, past questions, and patient vignette, generate a specific question to refine the current differential diagnosis. Return your reasoning and next question.",
            'late_questions': "You are a questioning agent (Late Stage). Based on narrowed differentials and previous dialogue, generate a focused question that would help confirm or eliminate the final 1-2 suspected diagnoses."
        }

    def determine_stage(self, iteration):
        """Determine current stage based on iteration number"""
        if iteration <= self.stage_thresholds['early'][1]:
            return 'early'
        elif iteration <= self.stage_thresholds['middle'][1]:
            return 'middle'
        else:
            return 'late'

    def generate_clinical_summary(self, patient_response, prev_vignette=""):
        """Generate clinical summary using summarizer prompt"""
        input_text = f"""
Instruction: {self.prompts['summarizer']}
Input: {patient_response} Previous Vignette: {prev_vignette}
Output: THINKING: 
"""
        
        output = self.model_client.generate(input_text, max_new_tokens=400)
        self.all_outputs['summarizer'].append(output)
        return output

    def generate_behavioral_analysis(self, patient_responses):
        """Generate behavioral analysis"""
        input_text = f"""
Instruction: {self.prompts['behavioral']}
Input: {' '.join(patient_responses)}
Output: THINKING: 
"""
        
        output = self.model_client.generate(input_text, max_new_tokens=300)
        self.all_outputs['behavioral'].append(output)
        return output

    def generate_treatment_plan(self, diagnosis, vignette):
        """Generate treatment plan"""
        input_text = f"""
Instruction: {self.prompts['treatment']}
Input: DIAGNOSIS: {diagnosis} VIGNETTE: {vignette}
Output: THINKING: 
"""
        
        output = self.model_client.generate(input_text, max_new_tokens=400)
        self.all_outputs['treatment'].append(output)
        return output

    def generate_diagnostic_reasoning(self, stage, vignette, prev_diagnosis="", conversation_history=""):
        """Generate diagnostic reasoning based on stage"""
        prompt_key = f"{stage}_diagnostic"
        
        if stage == 'early':
            input_text = f"""
Instruction: {self.prompts[prompt_key]}
Input: {vignette}
Output: THINKING:
"""
        elif stage == 'middle':
            input_text = f"""
Instruction: {self.prompts[prompt_key]}
Input: VIGNETTE: {vignette} PREVIOUS DIAGNOSIS: {prev_diagnosis} CONVERSATION: {conversation_history}
Output: THINKING:
"""
        else:  # late
            input_text = f"""
Instruction: {self.prompts[prompt_key]}
Input: VIGNETTE: {vignette} FULL CONVERSATION: {conversation_history}
Output: THINKING:
"""
        
        output = self.model_client.generate(input_text, max_new_tokens=400)
        self.all_outputs[prompt_key].append(output)
        return output

    def generate_question(self, stage, vignette, diagnosis, prev_questions, conversation_history):
        """Generate question based on stage"""
        prompt_key = f"{stage}_questions"
        
        if stage == 'early':
            input_text = f"""
Instruction: {self.prompts[prompt_key]}
Input: VIGNETTE: {vignette} DIAGNOSIS: {diagnosis} PREVIOUS Questions: {prev_questions} Conversation History: {conversation_history}
Output: THINKING:
"""
        elif stage == 'middle':
            input_text = f"""
Instruction: {self.prompts[prompt_key]}
Input: VIGNETTE: {vignette} CURRENT DIAGNOSIS: {diagnosis} PREVIOUS Questions: {prev_questions} CONVERSATION: {conversation_history}
Output: THINKING:
"""
        else:  # late
            input_text = f"""
Instruction: {self.prompts[prompt_key]}
Input: VIGNETTE: {vignette} NARROWED DIFFERENTIALS: {diagnosis} PREVIOUS DIALOGUE: {conversation_history}
Output: THINKING:
"""
        
        output = self.model_client.generate(input_text, max_new_tokens=400)
        self.all_outputs[prompt_key].append(output)
        return output

    def save_all_outputs(self):
        """Save all outputs to respective JSON files"""
        file_mappings = {
            'summarizer': 'all_summarizer_outputs.json',
            'behavioral': 'all_behavioral_analyses.json',
            'treatment': 'all_treatment_outputs.json',
            'early_diagnostic': 'ED.json',
            'middle_diagnostic': 'MD.json',
            'late_diagnostic': 'LD.json',
            'early_questions': 'E.json',
            'middle_questions': 'M.json',
            'late_questions': 'L.json'
        }
        
        for key, filename in file_mappings.items():
            if self.all_outputs[key]:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(self.all_outputs[key], f, indent=2, ensure_ascii=False)
                print(f"💾 Saved {filename}")

    def check_for_end_condition(self, diagnostic_output):
        """Check if the diagnostic output contains END signal"""
        return "END" in diagnostic_output.upper()


class PatientAgent:
    def __init__(self, model_client):
        self.model_client = model_client
        self.patient_profile = {}
        self.conversation_history = []
    
    def generate_response(self, doctor_question, patient_context=""):
        """Generate patient response to doctor's question"""
        prompt = f"""
You are a 35-year-old office worker with persistent headaches for 3 days. The pain is throbbing, located in your temples, and rates about 6/10 in intensity. You've tried ibuprofen but it only helps temporarily. You're worried because you've never had headaches this severe before.

Doctor asks: {doctor_question}

Respond naturally as the patient:
"""
        
        try:
            response = self.model_client.generate(prompt, max_new_tokens=150)
            # Extract just the patient response part
            if "ANSWER:" in response:
                patient_response = response.split("ANSWER:")[-1].strip()
            elif "Patient:" in response:
                patient_response = response.split("Patient:")[-1].strip()
            else:
                # Take the response after the prompt
                lines = response.split('\n')
                for line in lines:
                    if line.strip() and not line.startswith('You are') and not line.startswith('Doctor'):
                        patient_response = line.strip()
                        break
                else:
                    patient_response = response.strip()
            
            return patient_response
            
        except Exception as e:
            print(f"❌ Patient agent error: {e}")
            return "I'm not sure how to respond to that."


def parse_and_format_conversation(conversation_list):
    """
    Parse conversation list and format as requested: speaker: ", message: "
    """
    print("\n" + "🔗" * 60)
    print("📋 PARSED CONVERSATION OUTPUT:")
    print("🔗" * 60)
    
    for entry in conversation_list:
        if ':' in entry:
            speaker, message = entry.split(':', 1)
            speaker = speaker.strip()
            message = message.strip()
            
            # Format as requested: speaker: ", message: "
            formatted_line = f'{speaker}: ", {message}: "'
            print(formatted_line)
    
    print("🔗" * 60)


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


def run_multi_stage_conversation():
    """Run the multi-stage clinical conversation"""
    # Test connection first
    if not test_connection():
        print("Please check your ENDPOINT_URL and HF_TOKEN")
        return

    print("\n" + "=" * 80)
    print("🏥 Starting Multi-Stage Clinical Diagnostic Conversation")
    print("=" * 80)

    # Initialize agents
    clinician_ai = MultiStageClinicianAI(model_client)
    patient_agent = PatientAgent(model_client)
    
    # Conversation tracking
    conversation = []
    prev_questions = []
    prev_vignette = ""
    patient_responses = []
    
    # Initial patient presentation
    conversation.append("Doctor: What brings you in today?")
    initial_response = "I am a 35-year-old office worker who has been experiencing persistent headaches for 3 days. The pain is throbbing, located in my temples, and rates about 6/10 in intensity. I've tried ibuprofen but it only helps temporarily. I'm worried because I've never had headaches this severe before."
    conversation.append(f"Patient: {initial_response}")
    patient_responses.append(initial_response)
    
    current_diagnosis = ""
    
    # Main conversation loop
    max_iterations = 12
    for iteration in range(max_iterations):
        current_stage = clinician_ai.determine_stage(iteration)
        
        print(f"\n{'='*25} Iteration {iteration+1} - {current_stage.upper()} STAGE {'='*25}")
        
        # 1. Clinical Summary Generation
        print("🔄 Generating clinical summary...")
        clinical_summary = clinician_ai.generate_clinical_summary(
            patient_responses[-1], prev_vignette
        )
        print("📋 Clinical Summary:")
        print(clinical_summary[:200] + "..." if len(clinical_summary) > 200 else clinical_summary)
        
        # 2. Behavioral Analysis (every few iterations)
        if iteration % 3 == 0:
            print("\n🔄 Generating behavioral analysis...")
            behavioral_analysis = clinician_ai.generate_behavioral_analysis(patient_responses)
            print("🧠 Behavioral Analysis:")
            print(behavioral_analysis[:200] + "..." if len(behavioral_analysis) > 200 else behavioral_analysis)
        
        # 3. Diagnostic Reasoning (stage-specific)
        print(f"\n🔄 Generating {current_stage} stage diagnostic reasoning...")
        diagnostic_reasoning = clinician_ai.generate_diagnostic_reasoning(
            current_stage, 
            clinical_summary, 
            current_diagnosis, 
            ' '.join(conversation)
        )
        print(f"🩺 {current_stage.title()} Stage Diagnosis:")
        print(diagnostic_reasoning[:200] + "..." if len(diagnostic_reasoning) > 200 else diagnostic_reasoning)
        
        # Check for END condition in late stage
        if current_stage == 'late' and clinician_ai.check_for_end_condition(diagnostic_reasoning):
            print("\n🏁 END condition detected. Generating final treatment plan...")
            treatment_plan = clinician_ai.generate_treatment_plan(diagnostic_reasoning, clinical_summary)
            print("💊 Treatment Plan:")
            print(treatment_plan[:300] + "..." if len(treatment_plan) > 300 else treatment_plan)
            break
        
        # 4. Question Generation (stage-specific)
        print(f"\n🔄 Generating {current_stage} stage question...")
        question_output = clinician_ai.generate_question(
            current_stage,
            clinical_summary,
            diagnostic_reasoning,
            prev_questions,
            ' '.join(conversation)
        )
        
        # Extract the actual question from the output
        doctor_question = question_output.split("ANSWER:")[-1].strip() if "ANSWER:" in question_output else question_output.strip()
        
        print(f"❓ {current_stage.title()} Stage Question:")
        print(question_output[:200] + "..." if len(question_output) > 200 else question_output)
        
        # 5. Patient Response
        print(f"\n🩺 Doctor: {doctor_question}")
        conversation.append(f"Doctor: {doctor_question}")
        prev_questions.append(doctor_question)
        
        patient_response = patient_agent.generate_response(doctor_question, prev_vignette)
        print(f"👤 Patient: {patient_response}")
        conversation.append(f"Patient: {patient_response}")
        patient_responses.append(patient_response)
        
        # Update for next iteration
        prev_vignette = clinical_summary
        current_diagnosis = diagnostic_reasoning
        
        print(f"\n{'='*80}")
    
    # Final treatment plan if not already generated
    if iteration == max_iterations - 1:
        print("\n🔄 Generating final treatment plan...")
        treatment_plan = clinician_ai.generate_treatment_plan(current_diagnosis, prev_vignette)
        print("💊 Final Treatment Plan:")
        print(treatment_plan)
    
    # Save all outputs
    print("\n💾 Saving all outputs to JSON files...")
    clinician_ai.save_all_outputs()
    
    # Save main conversation
    conversation_data = {
        "conversation": conversation,
        "patient_responses": patient_responses,
        "final_diagnosis": current_diagnosis,
        "total_iterations": iteration + 1,
        "timestamp": datetime.now().isoformat(),
        "metadata": {
            "endpoint_url": ENDPOINT_URL,
            "model_parameters": {
                "max_new_tokens": 400,
                "temperature": 0.7,
                "do_sample": True,
                "return_full_text": True
            }
        }
    }
    
    with open("multi_stage_conversation.json", "w", encoding="utf-8") as f:
        json.dump(conversation_data, f, indent=2, ensure_ascii=False)
    
    print("💾 Main conversation saved to multi_stage_conversation.json")
    
    # PARSE AND FORMAT THE CONVERSATION AS REQUESTED
    print("\n🔄 Parsing conversation for formatted output...")
    parse_and_format_conversation(conversation)
    
    # Also save the formatted conversation to a separate file
    formatted_conversation = []
    for entry in conversation:
        if ':' in entry:
            speaker, message = entry.split(':', 1)
            speaker = speaker.strip()
            message = message.strip()
            formatted_line = f'{speaker}: ", {message}: "'
            formatted_conversation.append(formatted_line)
    
    with open("formatted_conversation.txt", "w", encoding="utf-8") as f:
        for line in formatted_conversation:
            f.write(line + "\n")
    
    print("💾 Formatted conversation saved to formatted_conversation.txt")
    print("✅ Multi-stage conversation finished!")


if __name__ == "__main__":
    print("🚀 Multi-Stage Clinical AI with HuggingFace Inference Endpoint")
    print(f"🔗 Endpoint: {ENDPOINT_URL}")
    print(f"🔑 Token: {HF_TOKEN[:8]}..." if HF_TOKEN else "❌ No token provided")
    
    # Run the multi-stage conversation
    run_multi_stage_conversation()
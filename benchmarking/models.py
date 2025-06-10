import os
import json
from openai import OpenAI
from datetime import datetime

# Initialize OpenAI client
try:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
except TypeError:
    print("Error: OPENAI_API_KEY not set. Please set the environment variable.")
    exit()

class OpenAIClinicianAI:
    def __init__(self, model="gpt-4o-mini"):
        self.model = model
        self.system_prompt = """
You are an expert AI clinician. Your goal is to conduct a diagnostic interview with a patient.
- Ask clear, targeted questions to understand the patient's symptoms and history.
- Show empathy and build rapport. Do not be overly robotic.
- Synthesize information to form a differential diagnosis.
- Think step-by-step.
- Conclude the conversation when you have sufficient information to propose a diagnosis and treatment plan.
"""

    def generate_response(self, conversation_history):
        messages = [{"role": "system", "content": self.system_prompt}]
        for turn in conversation_history:
            role = "assistant" if turn['speaker'] == "Doctor" else "user"
            messages.append({"role": role, "content": turn['message']})

        response = client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.7,
            max_tokens=300,
        )
        return response.choices[0].message.content.strip()

class PatientAgent:
    def __init__(self, model="gpt-4o-mini"):
        self.model = model
        self.system_prompt = """
You are roleplaying a patient. Here is your scenario:
You are a 35-year-old office worker who has been experiencing persistent headaches for the past 3 days.
- The pain is a throbbing sensation, mainly in your temples.
- On a scale of 1 to 10, the pain is about a 6/10, sometimes reaching 7/10.
- You've taken ibuprofen, but it provides only temporary relief for an hour or two.
- You are getting worried because you've never had headaches this severe or persistent before.
- You are otherwise healthy with no significant medical history.
- Respond naturally to the doctor's questions based on this profile. You are a little anxious about the situation. Keep your responses concise.
"""

    def generate_response(self, conversation_history):
        messages = [{"role": "system", "content": self.system_prompt}]
        for turn in conversation_history:
            role = "user" if turn['speaker'] == "Patient" else "assistant"
            messages.append({"role": role, "content": turn['message']})

        response = client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.8,
            max_tokens=150,
        )
        return response.choices[0].message.content.strip()

def run_openai_conversation(max_turns=10):
    ai_clinician = OpenAIClinicianAI()
    patient_agent = PatientAgent()
    
    patient_scenario = "A 35-year-old office worker with a 3-day history of persistent, severe headaches."
    
    # Initial patient response to start the conversation
    patient_response = "Hi doctor, I've been having these really bad headaches for a few days now and they're not going away."
    conversation_history = [{"speaker": "Patient", "message": patient_response}]
    
    print(f"Patient: {patient_response}")

    for i in range(max_turns):
        print(f"\n--- Turn {i+1} ---")
        
        # 1. Get Doctor's response
        doctor_question = ai_clinician.generate_response(conversation_history)
        print(f"❓ Doctor: {doctor_question}")
        conversation_history.append({"speaker": "Doctor", "message": doctor_question})
        
        # Check for end condition from doctor
        if "recommend" in doctor_question.lower() or "plan is to" in doctor_question.lower() or "propose we" in doctor_question.lower():
             print("\n🏁 Doctor concluding conversation.")
             break

        # 2. Get Patient's response
        patient_response = patient_agent.generate_response(conversation_history)
        print(f"💬 Patient: {patient_response}")
        conversation_history.append({"speaker": "Patient", "message": patient_response})

    print("\n✅ Conversation finished.")
    
    # Save conversation to file
    output_data = {
        "patient_scenario": patient_scenario,
        "conversation": conversation_history
    }
    
    output_filename = f"openai_doctor_conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_filename, "w") as f:
        json.dump(output_data, f, indent=2)
        
    print(f"Conversation saved to {output_filename}")
    return output_filename

if __name__ == '__main__':
    run_openai_conversation()

from transformers import AutoTokenizer, AutoModelForCausalLM

model_id = "CodCodingCode/llama-3.1-8b-grpo-v1.2"

# Load tokenizer and model
tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    device_map="auto",  # or "cuda:0" if you use one GPU
    torch_dtype="auto",  # uses fp16 if possible
)

convo = []
prev_questions = []
convo.append("Doctor: What brings you in today?")
patient_response = "I am 14. I am a male. I have pain in my stomach. I dont think its a stomach ache. I have had it for 2 days. It is a sharp pain. It is worse when I eat. I have not had any fever or vomiting. I am not sure if I have had diarrhea. I have been feeling tired."
convo.append(f"Patient: {patient_response}")
prev_vignette = ""

for i in range (10):
    # Create a sample input
    input_text = f"""

    Instruction: You are a clinical summarizer. Given a transcript of a doctor–patient dialogue, extract a structured clinical vignette summarizing the key symptoms, relevant history, and any diagnostic clues.
    Input: {patient_response} Previous Vignette: {prev_vignette}
    Output: THINKING: 
    """


    # Tokenize and generate
    inputs = tokenizer(input_text, return_tensors="pt").to(model.device)
    outputs = model.generate(**inputs, max_new_tokens=400)

    raw_output = tokenizer.decode(outputs[0], skip_special_tokens=True)
    output = raw_output.split("ANSWER:")[-1].strip()
    print(raw_output)

    input_text2 = f"""
    Instruction: You are a diagnostic reasoning model (Early Stage). Based on the patient vignette and early-stage observations, generate a list of plausible diagnoses with reasoning. Focus on broad differentials, considering common and uncommon conditions
    Input: {output}
    Output: THINKING:
    """
    inputs = tokenizer(input_text2, return_tensors="pt").to(model.device)
    outputs = model.generate(**inputs, max_new_tokens=400)
    raw_output = tokenizer.decode(outputs[0], skip_special_tokens=True)
    output2 = raw_output.split("ANSWER:")[-1].strip()
    print(raw_output)


    input_text3 = f"""
    Instruction: You are a questioning agent (Early Stage). Your task is to propose highly relevant early-stage questions that can open the differential diagnosis widely. Use epidemiology, demographics, and vague presenting symptoms as guides.
    Input: VIGNETTE: {output} DIAGNOSIS: {output2} PREVIOUS Questions: {prev_questions} Conversation History: {convo}
    Output: THINKING:
    """

    inputs = tokenizer(input_text3, return_tensors="pt").to(model.device)
    outputs = model.generate(**inputs, max_new_tokens=400)
    if i == 5:
        print(output2)
        break

    raw_output = tokenizer.decode(outputs[0], skip_special_tokens=True)
    doctor_output = raw_output.split("ANSWER:")[-1].strip()
    print(raw_output)


    print(f"{doctor_output}")
    convo.append(f"Doctor: {doctor_output}")
    prev_questions.append(doctor_output)

    patient_response = str(input("Patient Response: "))
    convo.append(f"Patient: {patient_response}")
    prev_vignette = output
print("finished!")
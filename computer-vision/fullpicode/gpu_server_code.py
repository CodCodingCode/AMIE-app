import torch
import numpy as np
from transformers import LlavaNextProcessor, LlavaNextForConditionalGeneration
from transformers import AutoTokenizer, AutoModelForCausalLM
from PIL import Image
from flask import Flask, request, jsonify
import json
import os
from datetime import datetime

app = Flask(__name__)

# ============================================================================
# MODEL PATHS AND TOKENS - YOUR ORIGINAL CONFIGURATION
# ============================================================================
LLAVA_MODEL_NAME = "llava-hf/llava-v1.6-mistral-7b-hf"
CLINICAL_MODEL_PATH = "CodCodingCode/llama-3.1-8b-clinical-V1.4"
HF_TOKEN = "hf_token"

# ============================================================================
# YOUR ORIGINAL MEDICAL ANALYSIS PROMPT - KEPT INTACT
# ============================================================================
GENERAL_MEDICAL_IMAGE_PROMPT = """
You are an AI-powered medical assistant. Given the attached photo of a patient's body part, object, or condition, analyze the image carefully and provide a detailed, medically relevant description that can assist a healthcare provider in understanding what is depicted.

Present your findings as a well-written, concise paragraph, not as a list or bullet points.

In your description, include the following where applicable:
- What is shown in the image (e.g. skin, joint, limb, face, wound, swelling, discoloration, visible abnormality, etc.)
- The body location if identifiable (e.g. arm, leg, hand, face, torso)
- Shape or structure (e.g. round, irregular, swollen, asymmetric, deformity present)
- Size estimate (approximate in cm, mm, or general terms)
- Color(s) and tone (e.g. normal skin tone, redness, bruising, pallor, abnormal colors)
- Texture or surface characteristics (e.g. smooth, rough, scaly, cracked, ulcerated)
- Edges or borders (e.g. well-defined, irregular, merging with surrounding tissue)
- Number or extent of findings (e.g. single abnormality, multiple areas, diffuse involvement)
- Symmetry or asymmetry
- Signs of inflammation (e.g. redness, heat, swelling)
- Signs of injury (e.g. cuts, bruises, bleeding, abrasions)
- Signs of infection (e.g. pus, discharge, crusting)
- Presence of medical devices, bandages, tattoos, or distinguishing marks
- Any other visible relevant information

If the image content is unclear or ambiguous, clearly state the uncertainty but still describe any observable details to the best of your ability.
"""

# ============================================================================
# LOAD ALL MODELS
# ============================================================================

print("🔄 Loading YOLOv5 model...")
yolo_model = torch.hub.load('ultralytics/yolov5', 'yolov5s')
print("✅ YOLOv5 loaded!")

print("🔄 Loading LLaVA-NeXT model...")
processor = LlavaNextProcessor.from_pretrained(LLAVA_MODEL_NAME)
model = LlavaNextForConditionalGeneration.from_pretrained(
    LLAVA_MODEL_NAME,
    torch_dtype=torch.float16,
    device_map="auto"
)
processor.tokenizer.padding_side = "left"
print("✅ LLaVA model loaded successfully!")

print(f"🔄 Loading model from {CLINICAL_MODEL_PATH}...")

# Load tokenizer
tokenizer = AutoTokenizer.from_pretrained(
    CLINICAL_MODEL_PATH, token=HF_TOKEN, use_fast=True, trust_remote_code=True
)

# Ensure pad token is set
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token
    print("🔧 Set pad_token to eos_token")

# Load model
clinical_model = AutoModelForCausalLM.from_pretrained(
    CLINICAL_MODEL_PATH,
    token=HF_TOKEN,
    device_map="auto",
    torch_dtype=torch.bfloat16,
    trust_remote_code=True,
    low_cpu_mem_usage=True,
)

# Set model to evaluation mode
clinical_model.eval()

print(f"✅ Clinical model loaded successfully!")
print(f"📊 Model device map: {getattr(clinical_model, 'hf_device_map', 'N/A')}")
print(f"🔧 Tokenizer vocab size: {len(tokenizer)}")

# ============================================================================
# YOUR ORIGINAL LocalModelInference CLASS - KEPT INTACT
# ============================================================================
class LocalModelInference:
    def __init__(self, model_path, device="auto"):
        self.model_path = model_path
        self.device = device
        self.tokenizer = tokenizer
        self.model = clinical_model

    def generate(self, prompt, max_new_tokens=800):
        """Generate text using the local model"""
        try:
            # Tokenize input
            inputs = self.tokenizer(
                prompt,
                return_tensors="pt",
                truncation=True,
                max_length=2048,  # Adjust based on your model's context length
                padding=False,
            )

            # Move inputs to the same device as model
            if hasattr(self.model, "device"):
                device = self.model.device
            else:
                device = next(self.model.parameters()).device

            inputs = {k: v.to(device) for k, v in inputs.items()}

            # Generate
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=max_new_tokens,
                    temperature=0.2,
                    do_sample=True,
                    repetition_penalty=1.1,
                    no_repeat_ngram_size=3,
                    pad_token_id=self.tokenizer.pad_token_id,
                    eos_token_id=self.tokenizer.eos_token_id,
                    early_stopping=False,
                )

            # Decode the generated text
            generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

            # Remove the input prompt from the generated text
            response = generated_text[len(prompt) :].strip()

            return response

        except Exception as e:
            print(f"❌ Generation failed: {e}")
            raise

    def clear_cache(self):
        """Clear GPU cache to free memory"""
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

# Initialize the inference client
print("🚀 Initializing local model...")
model_client = LocalModelInference(CLINICAL_MODEL_PATH)

# ============================================================================
# YOUR ORIGINAL HELPER FUNCTIONS - KEPT INTACT
# ============================================================================

def save_to_json(data, filename="clinical_conversation_log.json"):
    """Save data to JSON file"""
    if os.path.exists(filename):
        with open(filename, "r") as f:
            existing_data = json.load(f)
    else:
        existing_data = []

    existing_data.append(data)

    with open(filename, "w") as f:
        json.dump(existing_data, f, indent=2)

def save_conversation_state(
    conversation_log, filename="clinical_conversation_log.json"
):
    """Save current conversation state to JSON file after each turn"""
    with open(filename, "w") as f:
        json.dump(conversation_log, f, indent=2)

def extract_thinking_and_answer(raw_output):
    """Extract THINKING and ANSWER sections from raw output"""
    thinking = ""
    answer = ""

    if "THINKING:" in raw_output and "ANSWER:" in raw_output:
        # Both sections present
        thinking_start = raw_output.find("THINKING:") + len("THINKING:")
        answer_start = raw_output.find("ANSWER:") + len("ANSWER:")

        thinking = raw_output[thinking_start : raw_output.find("ANSWER:")].strip()
        answer = raw_output[answer_start:].strip()

        # Clean up common artifacts
        answer = answer.replace("STOP HERE", "").replace("Do not add", "").strip()

    elif "THINKING:" in raw_output:
        # Only thinking section
        thinking_start = raw_output.find("THINKING:") + len("THINKING:")
        thinking = raw_output[thinking_start:].strip()
        answer = ""

    elif "ANSWER:" in raw_output:
        # Only answer section
        answer_start = raw_output.find("ANSWER:") + len("ANSWER:")
        answer = raw_output[answer_start:].strip()
        answer = answer.replace("STOP HERE", "").replace("Do not add", "").strip()
        thinking = ""

    else:
        # Neither section, treat entire output as answer
        answer = raw_output.strip()
        thinking = ""

    return thinking, answer

def clean_doctor_question(raw_question):
    """Clean and extract just the question from doctor output"""

    # Remove common prefixes and artifacts
    cleaned = raw_question.strip()

    # Remove THINKING/ANSWER artifacts
    cleaned = cleaned.replace("THINKING:", "").replace("ANSWER:", "")

    # Remove instructions and meta-text
    lines = cleaned.split("\n")
    question_lines = []

    for line in lines:
        line = line.strip()
        # Skip meta-commentary lines
        if any(
            skip_phrase in line.lower()
            for skip_phrase in [
                "this question is different",
                "therefore, asking about",
                "specifically, knowing what",
                "additionally, vital sign",
                "whereas now i want",
                "the vignette indicates",
                "since her symptoms",
                "understanding her physical",
                "based on the patient",
                "given the current",
                "to better understand",
            ]
        ):
            continue

        # Look for actual questions
        if "?" in line and len(line) > 10:
            question_lines.append(line)

    if question_lines:
        # Return the first clean question found
        return question_lines[0].strip()

    # Fallback: look for question patterns in the original text
    sentences = cleaned.split(".")
    for sentence in sentences:
        sentence = sentence.strip()
        if "?" in sentence and len(sentence) > 10:
            return sentence.strip() + ("?" if not sentence.endswith("?") else "")

    # Last resort: return first reasonable length sentence that sounds like a question
    sentences = cleaned.split(".")
    for sentence in sentences:
        sentence = sentence.strip()
        if 10 < len(sentence) < 150 and any(
            q_word in sentence.lower()
            for q_word in [
                "what",
                "when",
                "where",
                "how",
                "why",
                "can you",
                "have you",
                "do you",
                "did you",
            ]
        ):
            return sentence.strip() + "?"

    # Final fallback
    return "Can you tell me more about your symptoms?"

# ============================================================================
# OBJECT DETECTION FUNCTIONS (NO CV2!)
# ============================================================================

def detect_objects_in_frame(image_array):
    """
    Run YOLOv5 object detection on frame (from Pi image)
    Returns: (has_person, confidence, detection_info)
    """
    try:
        results = yolo_model(image_array)
        detections = results.xyxy[0].cpu().numpy()
        
        # Look for person (class 0) with confidence > 0.5
        person_detections = []
        for detection in detections:
            x1, y1, x2, y2, conf, cls = detection
            if int(cls) == 0 and conf > 0.5:  # person class
                person_detections.append({
                    'bbox': [int(x1), int(y1), int(x2), int(y2)],
                    'confidence': float(conf),
                    'area': (x2-x1) * (y2-y1)
                })
        
        if person_detections:
            # Return the detection with highest confidence
            best_detection = max(person_detections, key=lambda x: x['confidence'])
            return True, best_detection['confidence'], best_detection
        else:
            return False, 0.0, None
            
    except Exception as e:
        print(f"❌ Object detection error: {e}")
        return False, 0.0, None

# ============================================================================
# YOUR ORIGINAL LLAVA ANALYSIS FUNCTION - KEPT INTACT
# ============================================================================

def analyze_image_with_llava(image, prompt, max_tokens=500):
    conversation = [
        {
            "role": "user",
            "content": [
                {"type": "image"},
                {"type": "text", "text": prompt},
            ],
        },
    ]
    text_prompt = processor.apply_chat_template(conversation, add_generation_prompt=True)
    inputs = processor(image, text_prompt, return_tensors="pt").to(model.device)

    with torch.no_grad():
        output = model.generate(
            **inputs,
            max_new_tokens=max_tokens,
            do_sample=False,
            temperature=0.1
        )

    response = processor.decode(output[0], skip_special_tokens=True)
    assistant_start = response.find("[/INST]") + len("[/INST]")
    if assistant_start > len("[/INST]") - 1:
        return response[assistant_start:].strip()
    else:
        return response

# ============================================================================
# CONVERSATION STATE STORAGE - YOUR ORIGINAL STRUCTURE
# ============================================================================
conversation_sessions = {}

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route("/")
def home():
    return "✅ Unified Medical AI Server (YOLOv5 + LLaVA + Clinical LLaMA) is Running!"

@app.route("/analyze_url", methods=["POST"])
def analyze_url():
    """YOUR ORIGINAL analyze_url ENDPOINT - KEPT INTACT"""
    data = request.json
    image_url = data.get("image_url")
    prompt = data.get("prompt", GENERAL_MEDICAL_IMAGE_PROMPT)

    if not image_url:
        return jsonify({"error": "Missing image_url"}), 400

    try:
        print(f"📥 Fetching image from: {image_url}")
        response = requests.get(image_url, stream=True, timeout=10)
        response.raise_for_status()
        image = Image.open(io.BytesIO(response.content)).convert("RGB")
    except Exception as e:
        return jsonify({"error": f"Failed to fetch/open image: {e}"}), 400

    try:
        print("🤖 Running LLaVA analysis...")
        result = analyze_image_with_llava(image, prompt)
        return jsonify({"result": result})
    except Exception as e:
        return jsonify({"error": f"Analysis error: {e}"}), 500

@app.route("/analyze_image", methods=["POST"])
def analyze_image():
    """YOUR ORIGINAL analyze_image ENDPOINT - KEPT INTACT"""
    if 'image' not in request.files:
        return jsonify({"error": "Missing image file"}), 400

    image_file = request.files['image']
    prompt = request.form.get("prompt", GENERAL_MEDICAL_IMAGE_PROMPT)

    try:
        image = Image.open(image_file).convert("RGB")
    except Exception as e:
        return jsonify({"error": f"Failed to open image: {e}"}), 400

    try:
        print("🤖 Running LLaVA analysis...")
        result = analyze_image_with_llava(image, prompt)
        return jsonify({"result": result})
    except Exception as e:
        return jsonify({"error": f"Analysis error: {e}"}), 500

@app.route("/analyze_frame", methods=["POST"])
def analyze_frame():
    """
    NEW ENDPOINT: Receives image from Pi, runs object detection, then LLaVA analysis
    """
    try:
        if 'image' not in request.files:
            return jsonify({"error": "Missing image file"}), 400

        image_file = request.files['image']
        custom_prompt = request.form.get("prompt", GENERAL_MEDICAL_IMAGE_PROMPT)
        
        # Read image as PIL and numpy array
        pil_image = Image.open(image_file).convert("RGB")
        image_array = np.array(pil_image)
        
        # Step 1: Object Detection
        print("🔍 Running object detection...")
        has_object, confidence, detection_info = detect_objects_in_frame(image_array)
        
        result = {
            "object_detected": has_object,
            "detection_confidence": confidence,
            "detection_info": detection_info,
            "analysis": None
        }
        
        # Step 2: If object detected, run LLaVA analysis
        if has_object:
            print(f"✅ Object detected with {confidence:.2f} confidence, running LLaVA analysis...")
            analysis = analyze_image_with_llava(pil_image, custom_prompt)
            result["analysis"] = analysis
            print(f"📝 Analysis complete: {analysis[:100]}...")
        else:
            print("❌ No object detected in frame")
            
        return jsonify(result)
        
    except Exception as e:
        print(f"❌ Error in analyze_frame: {e}")
        return jsonify({"error": f"Analysis failed: {str(e)}"}), 500

@app.route("/detect_only", methods=["POST"])
def detect_only():
    """YOUR ORIGINAL detect_only ENDPOINT - KEPT INTACT"""
    try:
        if 'image' not in request.files:
            return jsonify({"error": "Missing image file"}), 400

        image_file = request.files['image']
        pil_image = Image.open(image_file).convert("RGB")
        image_array = np.array(pil_image)
        
        has_object, confidence, detection_info = detect_objects_in_frame(image_array)
        
        return jsonify({
            "object_detected": has_object,
            "detection_confidence": confidence,
            "detection_info": detection_info
        })
        
    except Exception as e:
        return jsonify({"error": f"Detection failed: {str(e)}"}), 500

# ============================================================================
# YOUR ORIGINAL CLINICAL AI CONVERSATION LOGIC - KEPT INTACT
# ============================================================================

@app.route("/start_conversation", methods=["POST"])
def start_conversation():
    """Initialize a new medical conversation session"""
    try:
        data = request.json
        session_id = data.get("session_id", f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        initial_image_analysis = data.get("image_analysis", "")
        
        # Initialize conversation state
        conversation_sessions[session_id] = {
            "created_at": datetime.now().isoformat(),
            "conversation_history": [],
            "previous_questions": [],
            "iteration": 0,
            "vignette": "",
            "image_analysis": initial_image_analysis
        }
        
        # Create initial clinical summary from image analysis
        if initial_image_analysis:
            input_text = f"""Instruction: You are a clinical summarizer. Given a transcript of a doctor–patient dialogue, extract a structured clinical vignette summarizing the key symptoms, relevant history, and any diagnostic clues.
Input: {initial_image_analysis} Previous Vignette: 
Output: THINKING: """
            
            print(f"🔄 Creating clinical summary for session {session_id}...")
            raw_output = model_client.generate(input_text, max_new_tokens=1000)
            thinking, answer = extract_thinking_and_answer(raw_output)
            
            conversation_sessions[session_id]["vignette"] = answer if answer else raw_output
            
            # Generate first question
            first_question = generate_question(session_id)
            
            return jsonify({
                "session_id": session_id,
                "question": first_question,
                "status": "conversation_started"
            })
        else:
            # Start with general question
            first_question = "What brings you in today? I can see you're showing me a skin condition."
            conversation_sessions[session_id]["conversation_history"].append(f"Doctor: {first_question}")
            
            return jsonify({
                "session_id": session_id,
                "question": first_question,
                "status": "conversation_started"
            })
    except Exception as e:
        print(f"❌ Error starting conversation: {e}")
        return jsonify({"error": str(e)}), 500

def generate_question(session_id):
    """Generate next question based on conversation state"""
    session = conversation_sessions[session_id]
    
    # Generate question based on current vignette and history
    input_text = f"""Instruction: You are a questioning agent (Early Stage). Your task is to propose highly relevant early-stage questions that can open the differential diagnosis widely. Use epidemiology, demographics, and vague presenting symptoms as guides.
Input: VIGNETTE: {session['vignette']} DIAGNOSIS: {session.get('current_diagnosis', '')} PREVIOUS Questions: {session['previous_questions']} Conversation History: {session['conversation_history']}
Output: THINKING:"""
    
    print(f"🔄 Generating question for session {session_id}...")
    raw_output = model_client.generate(input_text, max_new_tokens=1000)
    thinking, answer = extract_thinking_and_answer(raw_output)
    
    # Clean the question
    question = clean_doctor_question(answer if answer else raw_output)
    
    # Update session
    session['conversation_history'].append(f"Doctor: {question}")
    session['previous_questions'].append(question)
    session['iteration'] += 1
    
    return question

@app.route("/continue_conversation", methods=["POST"])
def continue_conversation():
    """Continue medical conversation with patient response"""
    try:
        data = request.json
        session_id = data.get("session_id")
        patient_response = data.get("patient_response")
        
        if session_id not in conversation_sessions:
            return jsonify({"error": "Invalid session ID"}), 400
            
        session = conversation_sessions[session_id]
        
        # Add patient response to history
        session['conversation_history'].append(f"Patient: {patient_response}")
        
        # Check if we should end conversation (after 5-6 questions)
        if session['iteration'] >= 5:
            # Generate final summary/diagnosis
            final_summary = generate_final_summary(session_id)
            return jsonify({
                "conversation_complete": True,
                "summary": final_summary,
                "session_id": session_id
            })
        
        # Update clinical summary with new information
        update_clinical_summary(session_id, patient_response)
        
        # Generate diagnostic reasoning
        generate_diagnostic_reasoning(session_id)
        
        # Generate treatment plan
        generate_treatment_plan(session_id)
        
        # Generate next question
        next_question = generate_question(session_id)
        
        return jsonify({
            "question": next_question,
            "conversation_complete": False,
            "session_id": session_id,
            "iteration": session['iteration']
        })
        
    except Exception as e:
        print(f"❌ Error continuing conversation: {e}")
        return jsonify({"error": str(e)}), 500

def update_clinical_summary(session_id, patient_response):
    """Update clinical vignette with new patient information"""
    session = conversation_sessions[session_id]
    
    input_text = f"""Instruction: You are a clinical summarizer. Given a transcript of a doctor–patient dialogue, extract a structured clinical vignette summarizing the key symptoms, relevant history, and any diagnostic clues.
Input: {patient_response} Previous Vignette: {session['vignette']}
Output: THINKING:"""
    
    raw_output = model_client.generate(input_text, max_new_tokens=800)
    thinking, answer = extract_thinking_and_answer(raw_output)
    
    # Update vignette
    session['vignette'] = answer if answer else raw_output

def generate_diagnostic_reasoning(session_id):
    """Generate diagnostic reasoning based on current state"""
    session = conversation_sessions[session_id]
    
    input_text = f"""Instruction: You are a diagnostic reasoning model (Early Stage). Based on the patient vignette and early-stage observations, generate a list of plausible diagnoses with reasoning. Focus on broad differentials, considering common and uncommon conditions
Input: {session['vignette']}
Output: THINKING:"""
    
    raw_output = model_client.generate(input_text, max_new_tokens=800)
    thinking, answer = extract_thinking_and_answer(raw_output)
    
    session['current_diagnosis'] = answer if answer else raw_output

def generate_treatment_plan(session_id):
    """Generate treatment plan based on current diagnosis"""
    session = conversation_sessions[session_id]
    
    input_text = f"""Instruction: You are a board-certified clinician. Based on the provided diagnosis and patient vignette, propose a realistic, evidence-based treatment plan suitable for initiation by a primary care physician or psychiatrist.
Input: Diagnosis: {session.get('current_diagnosis', '')} Vignette: {session['vignette']}
Output: THINKING:"""
    
    raw_output = model_client.generate(input_text, max_new_tokens=1000)
    thinking, answer = extract_thinking_and_answer(raw_output)
    
    session['current_treatment'] = answer if answer else raw_output

def generate_final_summary(session_id):
    """Generate final diagnosis and treatment recommendation"""
    session = conversation_sessions[session_id]
    
    # Generate final diagnosis using Late Stage reasoning
    diagnosis_input = f"""Instruction: You are a diagnostic reasoning model (Late Stage). Based on the final patient vignette summary and full conversation, provide the most likely diagnosis with structured reasoning. Confirm diagnostic certainty and include END if no more questioning is necessary.
Input: {session['vignette']}
Full Conversation: {' '.join(session['conversation_history'])}
Output: THINKING:"""
    
    diagnosis_output = model_client.generate(diagnosis_input, max_new_tokens=1000)
    thinking, diagnosis = extract_thinking_and_answer(diagnosis_output)
    final_diagnosis = diagnosis if diagnosis else diagnosis_output
    
    # Generate final treatment plan
    treatment_input = f"""Instruction: You are a board-certified clinician. Based on the provided diagnosis and patient vignette, propose a realistic, evidence-based treatment plan suitable for initiation by a primary care physician or psychiatrist.
Input: Diagnosis: {final_diagnosis} Vignette: {session['vignette']}
Output: THINKING:"""
    
    treatment_output = model_client.generate(treatment_input, max_new_tokens=1000)
    thinking, treatment = extract_thinking_and_answer(treatment_output)
    final_treatment = treatment if treatment else treatment_output
    
    # Combine into summary
    summary = f"DIAGNOSIS:\n{final_diagnosis}\n\nRECOMMENDED TREATMENT:\n{final_treatment}"
    
    # Save session to file using your original structure
    session['final_diagnosis'] = final_diagnosis
    session['final_treatment'] = final_treatment
    session['completed_at'] = datetime.now().isoformat()
    
    filename = f"session_{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w') as f:
        json.dump(session, f, indent=2)
    
    return summary

@app.route("/get_session", methods=["GET"])
def get_session():
    """Get session information"""
    session_id = request.args.get("session_id")
    if session_id in conversation_sessions:
        return jsonify(conversation_sessions[session_id])
    else:
        return jsonify({"error": "Session not found"}), 404

@app.route("/clear_cache", methods=["POST"])
def clear_cache():
    """Clear GPU cache manually"""
    model_client.clear_cache()
    return jsonify({"status": "cache_cleared"})

if __name__ == "__main__":
    print("🚀 Unified Medical AI Server with ALL Original Functionality")
    print(f"🔍 YOLOv5: Loaded")
    print(f"🖼️  LLaVA: {LLAVA_MODEL_NAME}")
    print(f"🩺 Clinical: {CLINICAL_MODEL_PATH}")
    print(f"🔑 Token: {HF_TOKEN[:8]}..." if HF_TOKEN else "❌ No token provided")
    print(f"🎮 GPU Available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"🔧 GPU Count: {torch.cuda.device_count()}")
        for i in range(torch.cuda.device_count()):
            props = torch.cuda.get_device_properties(i)
            print(f"   GPU {i}: {props.name} ({props.total_memory / 1e9:.1f} GB)")
    
    app.run(host="0.0.0.0", port=7860, debug=False)
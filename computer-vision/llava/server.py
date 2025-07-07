import json
import os
from datetime import datetime
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, LlavaNextProcessor, LlavaNextForConditionalGeneration
from PIL import Image
import requests
from flask import Flask, request, jsonify
import io

# ============================================================================
# CONFIGURATION - REPLACE WITH YOUR ACTUAL PATHS AND TOKENS
# ============================================================================
CLINICAL_MODEL_PATH = "CodCodingCode/llama-3.1-8b-clinical-V1.4"
VISION_MODEL_NAME = "llava-hf/llava-v1.6-mistral-7b-hf"

# Get HuggingFace token ONLY for the clinical model (if needed)
HF_TOKEN = os.getenv("HUGGINGFACE_TOKEN")

app = Flask(__name__)

# ============================================================================
# VISION ANALYSIS SETUP (LLaVA is open source - no token needed)
# ============================================================================
print("🔄 Loading LLaVA-NeXT vision model...")
try:
    # LLaVA is public - load without token
    vision_processor = LlavaNextProcessor.from_pretrained(VISION_MODEL_NAME)
    vision_model = LlavaNextForConditionalGeneration.from_pretrained(
        VISION_MODEL_NAME,
        torch_dtype=torch.float16,
        device_map="auto"
    )
    
    vision_processor.tokenizer.padding_side = "left"
    print("✅ Vision model loaded successfully!")
    
except Exception as e:
    print(f"❌ Error loading vision model: {e}")
    print("💡 This shouldn't happen - LLaVA is open source!")
    print(f"   Error details: {e}")
    exit(1)

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

def analyze_image_with_llava(image, prompt=GENERAL_MEDICAL_IMAGE_PROMPT, max_tokens=500):
    """Analyze medical image using LLaVA-NeXT"""
    conversation = [
        {
            "role": "user",
            "content": [
                {"type": "image"},
                {"type": "text", "text": prompt},
            ],
        },
    ]
    text_prompt = vision_processor.apply_chat_template(conversation, add_generation_prompt=True)
    inputs = vision_processor(image, text_prompt, return_tensors="pt").to(vision_model.device)

    with torch.no_grad():
        output = vision_model.generate(
            **inputs,
            max_new_tokens=max_tokens,
            do_sample=False,
            temperature=0.1
        )

    response = vision_processor.decode(output[0], skip_special_tokens=True)
    assistant_start = response.find("[/INST]") + len("[/INST]")
    if assistant_start > len("[/INST]") - 1:
        return response[assistant_start:].strip()
    else:
        return response

# ============================================================================
# CLINICAL AI SETUP
# ============================================================================
class LocalModelInference:
    def __init__(self, model_path, device="auto"):
        self.model_path = model_path
        self.device = device

        print(f"🔄 Loading clinical model from {model_path}...")

        # Load tokenizer
        try:
            if HF_TOKEN:
                self.tokenizer = AutoTokenizer.from_pretrained(
                    model_path, token=HF_TOKEN, use_fast=True, trust_remote_code=True
                )
            else:
                self.tokenizer = AutoTokenizer.from_pretrained(
                    model_path, use_fast=True, trust_remote_code=True
                )
        except Exception as e:
            print(f"❌ Error loading tokenizer: {e}")
            print("💡 Try setting HuggingFace token: export HUGGINGFACE_TOKEN=your_token")
            raise

        # Ensure pad token is set
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
            print("🔧 Set pad_token to eos_token")

        # Load model
        try:
            if HF_TOKEN:
                self.model = AutoModelForCausalLM.from_pretrained(
                    model_path,
                    token=HF_TOKEN,
                    device_map=device,
                    torch_dtype=torch.bfloat16,
                    trust_remote_code=True,
                    low_cpu_mem_usage=True,
                )
            else:
                self.model = AutoModelForCausalLM.from_pretrained(
                    model_path,
                    device_map=device,
                    torch_dtype=torch.bfloat16,
                    trust_remote_code=True,
                    low_cpu_mem_usage=True,
                )
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            print("💡 Try setting HuggingFace token: export HUGGINGFACE_TOKEN=your_token")
            raise

        # Set model to evaluation mode
        self.model.eval()

        print(f"✅ Clinical model loaded successfully!")
        print(f"📊 Model device map: {getattr(self.model, 'hf_device_map', 'N/A')}")

    def generate(self, prompt, max_new_tokens=800):
        """Generate text using the local clinical model"""
        try:
            # Tokenize input
            inputs = self.tokenizer(
                prompt,
                return_tensors="pt",
                truncation=True,
                max_length=2048,
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
            response = generated_text[len(prompt):].strip()

            return response

        except Exception as e:
            print(f"❌ Generation failed: {e}")
            raise

    def clear_cache(self):
        """Clear GPU cache to free memory"""
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

# Initialize the clinical inference client
print("🚀 Initializing clinical model...")
clinical_model = LocalModelInference(CLINICAL_MODEL_PATH)

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================
def save_conversation_state(conversation_log, filename="clinical_conversation_log.json"):
    """Save current conversation state to JSON file after each turn"""
    with open(filename, "w") as f:
        json.dump(conversation_log, f, indent=2)

def extract_thinking_and_answer(raw_output):
    """Extract THINKING and ANSWER sections from raw output"""
    thinking = ""
    answer = ""

    if "THINKING:" in raw_output and "ANSWER:" in raw_output:
        thinking_start = raw_output.find("THINKING:") + len("THINKING:")
        answer_start = raw_output.find("ANSWER:") + len("ANSWER:")
        thinking = raw_output[thinking_start:raw_output.find("ANSWER:")].strip()
        answer = raw_output[answer_start:].strip()
        answer = answer.replace("STOP HERE", "").replace("Do not add", "").strip()
    elif "THINKING:" in raw_output:
        thinking_start = raw_output.find("THINKING:") + len("THINKING:")
        thinking = raw_output[thinking_start:].strip()
        answer = ""
    elif "ANSWER:" in raw_output:
        answer_start = raw_output.find("ANSWER:") + len("ANSWER:")
        answer = raw_output[answer_start:].strip()
        answer = answer.replace("STOP HERE", "").replace("Do not add", "").strip()
        thinking = ""
    else:
        answer = raw_output.strip()
        thinking = ""

    return thinking, answer

def clean_doctor_question(raw_question):
    """Clean and extract just the question from doctor output"""
    cleaned = raw_question.strip()
    cleaned = cleaned.replace("THINKING:", "").replace("ANSWER:", "")
    
    lines = cleaned.split("\n")
    question_lines = []

    for line in lines:
        line = line.strip()
        if any(skip_phrase in line.lower() for skip_phrase in [
            "this question is different", "therefore, asking about",
            "specifically, knowing what", "additionally, vital sign",
            "whereas now i want", "the vignette indicates"
        ]):
            continue
        if "?" in line and len(line) > 10:
            question_lines.append(line)

    if question_lines:
        return question_lines[0].strip()

    # Fallback logic
    sentences = cleaned.split(".")
    for sentence in sentences:
        sentence = sentence.strip()
        if "?" in sentence and len(sentence) > 10:
            return sentence.strip() + ("?" if not sentence.endswith("?") else "")

    return "Can you tell me more about your symptoms?"

def test_models():
    """Test both models"""
    try:
        print("🔄 Testing clinical model...")
        result = clinical_model.generate("Hello, this is a test.", max_new_tokens=20)
        print(f"✅ Clinical model working! Test: {result[:50]}...")
        
        print("🔄 Testing vision model...")
        # Create a simple test image
        test_image = Image.new('RGB', (100, 100), color='red')
        vision_result = analyze_image_with_llava(test_image, "What do you see?", max_tokens=50)
        print(f"✅ Vision model working! Test: {vision_result[:50]}...")
        
        return True
    except Exception as e:
        print(f"❌ Model testing failed: {e}")
        return False

# ============================================================================
# FLASK ROUTES
# ============================================================================
@app.route("/")
def home():
    return "✅ Combined Medical Vision + AI Doctor Server is Running!"

@app.route("/analyze_image_url", methods=["POST"])
def analyze_image_url():
    """Analyze image from URL"""
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
        print("🤖 Running vision analysis...")
        result = analyze_image_with_llava(image, prompt)
        return jsonify({"result": result})
    except Exception as e:
        return jsonify({"error": f"Analysis error: {e}"}), 500

@app.route("/analyze_image_upload", methods=["POST"])
def analyze_image_upload():
    """Analyze uploaded image"""
    if 'image' not in request.files:
        return jsonify({"error": "Missing image file"}), 400

    image_file = request.files['image']
    prompt = request.form.get("prompt", GENERAL_MEDICAL_IMAGE_PROMPT)

    try:
        image = Image.open(image_file).convert("RGB")
    except Exception as e:
        return jsonify({"error": f"Failed to open image: {e}"}), 400

    try:
        print("🤖 Running vision analysis...")
        result = analyze_image_with_llava(image, prompt)
        return jsonify({"result": result})
    except Exception as e:
        return jsonify({"error": f"Analysis error: {e}"}), 500

@app.route("/start_diagnosis", methods=["POST"])
def start_diagnosis():
    """Start diagnostic conversation with optional image analysis"""
    data = request.json
    initial_complaint = data.get("initial_complaint", "")
    image_analysis = data.get("image_analysis", "")
    
    # Combine initial complaint with image analysis
    full_patient_info = initial_complaint
    if image_analysis:
        full_patient_info += f"\n\nAdditional visual findings from medical image: {image_analysis}"
    
    # Initialize conversation
    conversation_log = {
        "timestamp": datetime.now().isoformat(),
        "initial_complaint": initial_complaint,
        "image_analysis": image_analysis,
        "full_patient_info": full_patient_info,
        "iterations": []
    }
    
    return jsonify({
        "message": "Diagnostic conversation started",
        "full_patient_info": full_patient_info,
        "conversation_id": conversation_log["timestamp"]
    })

# ============================================================================
# MAIN DIAGNOSTIC CONVERSATION FUNCTION
# ============================================================================
def run_conversation_with_vision():
    """Run the complete diagnostic conversation with optional vision analysis"""
    
    # Test models first
    if not test_models():
        print("❌ Please check your model paths and tokens")
        return

    print("\n" + "=" * 60)
    print("🏥 Medical Vision + AI Doctor System")
    print("=" * 60)

    # Step 1: Optional image analysis
    image_analysis = ""
    use_image = input("📸 Do you have a medical image to analyze? (y/n): ").strip().lower()
    
    if use_image == 'y':
        image_path = input("📁 Enter the path to your medical image: ").strip()
        try:
            image = Image.open(image_path).convert("RGB")
            print("🔄 Analyzing medical image...")
            image_analysis = analyze_image_with_llava(image, GENERAL_MEDICAL_IMAGE_PROMPT)
            print(f"\n📋 Medical Image Analysis:")
            print(f"🔍 {image_analysis}")
            print("\n" + "-" * 50)
        except Exception as e:
            print(f"❌ Error analyzing image: {e}")
            image_analysis = ""

    # Step 2: Get initial complaint
    print("\n👩‍⚕️ Doctor: What brings you in today?")
    initial_complaint = input("👤 Patient: ").strip()

    # Step 3: Combine initial complaint with image analysis
    full_patient_info = initial_complaint
    if image_analysis:
        full_patient_info += f"\n\nAdditional visual findings from medical image: {image_analysis}"
        print(f"\n📝 Combined patient information:")
        print(f"💬 Initial complaint: {initial_complaint}")
        print(f"🔍 Image analysis: {image_analysis}")

    # Initialize conversation log
    conversation_log = {
        "timestamp": datetime.now().isoformat(),
        "initial_complaint": initial_complaint,
        "image_analysis": image_analysis,
        "full_patient_info": full_patient_info,
        "iterations": []
    }

    # Step 4: Start diagnostic conversation
    convo = []
    prev_questions = []
    convo.append("Doctor: What brings you in today?")
    convo.append(f"Patient: {full_patient_info}")
    
    patient_response = full_patient_info
    prev_vignette = ""

    for i in range(6):  # Maximum 6 iterations
        print(f"\n{'='*20} Iteration {i+1} {'='*20}")

        iteration_data = {
            "iteration": i + 1,
            "clinical_summary": {},
            "diagnostic_reasoning": {},
            "question_generation": {},
            "treatment_plan": {},
            "patient_response": patient_response,
            "conversation_history": convo.copy(),
        }

        # Clear GPU cache periodically
        if i % 2 == 0:
            clinical_model.clear_cache()

        # 1. Clinical Summary Generation
        input_text = f"""Instruction: You are a clinical summarizer. Given a transcript of a doctor–patient dialogue, extract a structured clinical vignette summarizing the key symptoms, relevant history, and any diagnostic clues.
Input: {patient_response} Previous Vignette: {prev_vignette}
Output: THINKING: """

        print("🔄 Generating clinical summary...")
        raw_output = clinical_model.generate(input_text, max_new_tokens=1000)
        thinking, answer = extract_thinking_and_answer(raw_output)

        iteration_data["clinical_summary"] = {
            "input": input_text,
            "raw_output": raw_output,
            "thinking": thinking,
            "answer": answer,
        }

        output = answer if answer else raw_output
        print("📋 Clinical Summary:")
        print(output[:300] + "..." if len(output) > 300 else output)

        # 2. Diagnostic Reasoning
        input_text2 = f"""Instruction: You are a diagnostic reasoning model (Early Stage). Based on the patient vignette and early-stage observations, generate a list of plausible diagnoses with reasoning. Focus on broad differentials, considering common and uncommon conditions
Input: {output}
Output: THINKING:"""

        print("🔄 Generating diagnostic reasoning...")
        raw_output2 = clinical_model.generate(input_text2, max_new_tokens=800)
        thinking2, answer2 = extract_thinking_and_answer(raw_output2)

        iteration_data["diagnostic_reasoning"] = {
            "input": input_text2,
            "raw_output": raw_output2,
            "thinking": thinking2,
            "answer": answer2,
        }

        output2 = answer2 if answer2 else raw_output2
        print("🩺 Diagnostic Reasoning:")
        print(output2[:300] + "..." if len(output2) > 300 else output2)

        # Check if we've reached the final iteration
        if i == 5:
            print("\n🏁 Reached maximum iterations. Final diagnosis:")
            print(output2)
            break

        # 3. Question Generation
        input_text3 = f"""Instruction: You are a questioning agent (Early Stage). Your task is to propose highly relevant early-stage questions that can open the differential diagnosis widely. Use epidemiology, demographics, and vague presenting symptoms as guides.
Input: VIGNETTE: {output} DIAGNOSIS: {output2} PREVIOUS Questions: {prev_questions} Conversation History: {convo}
Output: THINKING:"""

        print("🔄 Generating next question...")
        raw_output3 = clinical_model.generate(input_text3, max_new_tokens=1000)
        thinking3, answer3 = extract_thinking_and_answer(raw_output3)

        iteration_data["question_generation"] = {
            "input": input_text3,
            "raw_output": raw_output3,
            "thinking": thinking3,
            "answer": answer3,
        }

        # Clean the doctor output to get just the question
        doctor_output = clean_doctor_question(answer3 if answer3 else raw_output3)
        print(f"❓ Next Question: {doctor_output}")

        # 4. Treatment Plan Generation
        input_text4 = f"""Instruction: You are a board-certified clinician. Based on the provided diagnosis and patient vignette, propose a realistic, evidence-based treatment plan suitable for initiation by a primary care physician or psychiatrist.
Input: Diagnosis: {output2} Vignette: {output}
Output: THINKING:"""

        print("🔄 Generating treatment plan...")
        raw_output4 = clinical_model.generate(input_text4, max_new_tokens=1000)
        thinking4, answer4 = extract_thinking_and_answer(raw_output4)

        iteration_data["treatment_plan"] = {
            "input": input_text4,
            "raw_output": raw_output4,
            "thinking": thinking4,
            "answer": answer4,
        }

        print("💊 Treatment Plan:")
        treatment_output = answer4 if answer4 else raw_output4
        print(treatment_output[:300] + "..." if len(treatment_output) > 300 else treatment_output)

        # Save conversation state
        conversation_log["iterations"].append(iteration_data)
        save_conversation_state(conversation_log)

        # Get patient response
        print(f"\n🩺 Doctor: {doctor_output}")
        convo.append(f"Doctor: {doctor_output}")
        prev_questions.append(doctor_output)

        patient_response = input("👤 Your response as the patient: ").strip()
        if not patient_response:
            patient_response = "I'm not sure what else to tell you."

        convo.append(f"Patient: {patient_response}")
        prev_vignette = output

    # Final cleanup and save
    save_conversation_state(conversation_log)
    print(f"\n📄 Complete conversation log saved to clinical_conversation_log.json")
    print("✅ Diagnostic conversation completed!")
    clinical_model.clear_cache()

# ============================================================================
# MAIN EXECUTION
# ============================================================================
if __name__ == "__main__":
    print("🚀 Combined Medical Vision + AI Doctor System")
    print(f"🔍 Vision Model: {VISION_MODEL_NAME}")
    print(f"🩺 Clinical Model: {CLINICAL_MODEL_PATH}")
    print(f"🎮 GPU Available: {torch.cuda.is_available()}")
    
    if torch.cuda.is_available():
        print(f"🔧 GPU Count: {torch.cuda.device_count()}")
        print(f"💾 GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")

    mode = input("\n🎯 Choose mode:\n1. Interactive Console (c)\n2. Web API Server (w)\nEnter choice: ").strip().lower()

    if mode == 'w':
        print("\n🌐 Starting web server...")
        app.run(host="0.0.0.0", port=7860, debug=True)
    else:
        print("\n💬 Starting interactive console...")
        run_conversation_with_vision()
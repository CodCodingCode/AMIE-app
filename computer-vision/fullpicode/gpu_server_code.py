#!/usr/bin/env python3
"""
Complete GPU Server for Medical Analysis
Fixed LLaVA output and added quick detection endpoint
"""

import os
import json
import time
import torch
import cv2
import numpy as np
from datetime import datetime
from PIL import Image
import io

# Flask for API
from flask import Flask, request, jsonify

# YOLO for object detection
import ultralytics
from ultralytics import YOLO

# Transformers for LLaVA and Clinical AI
from transformers import (
    AutoTokenizer, AutoModelForCausalLM,
    LlavaNextProcessor, LlavaNextForConditionalGeneration
)

# ============================================================================
# CONFIGURATION
# ============================================================================
YOLO_MODEL_PATH = "yolov8n.pt"
VISION_MODEL_NAME = "llava-hf/llava-v1.6-mistral-7b-hf"
CLINICAL_MODEL_PATH = "CodCodingCode/llama-3.1-8b-clinical-V1.4"

HF_TOKEN = "_"

HAND_CONFIDENCE_THRESHOLD = 0.2  # Lowered for better detection
TARGET_CLASSES = ['person', 'hand']

app = Flask(__name__)

# Global model storage
models = {
    'yolo': None,
    'vision_processor': None,
    'vision_model': None,
    'clinical_tokenizer': None,
    'clinical_model': None
}

# ============================================================================
# BASE PATIENT INFORMATION
# ============================================================================
BASE_PATIENT_INFO = """
Patient presents for medical evaluation with concerns about a visible condition. 
Initial assessment indicates the need for further clinical questioning to establish 
proper diagnosis and treatment plan. Patient appears cooperative and willing to 
provide medical history. Vital signs stable at time of presentation.
"""

# ============================================================================
# MEDICAL PROMPTS
# ============================================================================
MEDICAL_IMAGE_ANALYSIS_PROMPT = """
You are an AI-powered medical assistant. Analyze this medical image and provide a detailed clinical description of what you observe. Focus on medically relevant findings that would assist in diagnosis.

Describe in a single paragraph what is shown in the image, including:
- Body part/location visible
- Any abnormalities, lesions, discoloration, or concerning findings
- Size, shape, and characteristics of any findings
- Signs of inflammation, injury, or infection
- Any other clinically relevant observations

Be specific and clinical in your description.
"""

# ============================================================================
# MODEL LOADING
# ============================================================================
def load_yolo_model():
    try:
        print("🔄 Loading YOLO model...")
        model = YOLO(YOLO_MODEL_PATH)
        print("✅ YOLO model loaded")
        return model
    except Exception as e:
        print(f"❌ YOLO load failed: {e}")
        return None

def load_vision_models():
    try:
        print("🔄 Loading LLaVA vision model...")
        processor = LlavaNextProcessor.from_pretrained(VISION_MODEL_NAME, token=HF_TOKEN)
        model = LlavaNextForConditionalGeneration.from_pretrained(
            VISION_MODEL_NAME,
            token=HF_TOKEN,
            torch_dtype=torch.float16,
            device_map="auto"
        )
        processor.tokenizer.padding_side = "left"
        print("✅ LLaVA model loaded")
        return processor, model
    except Exception as e:
        print(f"❌ LLaVA load failed: {e}")
        return None, None

def load_clinical_model():
    try:
        print("🔄 Loading clinical model...")
        tokenizer = AutoTokenizer.from_pretrained(CLINICAL_MODEL_PATH, token=HF_TOKEN, trust_remote_code=True)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        model = AutoModelForCausalLM.from_pretrained(
            CLINICAL_MODEL_PATH,
            token=HF_TOKEN,
            device_map="auto",
            torch_dtype=torch.bfloat16,
            trust_remote_code=True,
            low_cpu_mem_usage=True
        )
        model.eval()
        print("✅ Clinical model loaded")
        return tokenizer, model
    except Exception as e:
        print(f"❌ Clinical model load failed: {e}")
        return None, None

def initialize_models():
    print("🚀 Initializing all models...")
    models['yolo'] = load_yolo_model()
    models['vision_processor'], models['vision_model'] = load_vision_models()
    models['clinical_tokenizer'], models['clinical_model'] = load_clinical_model()
    
    success = all(model is not None for model in models.values())
    if success:
        print("✅ All models loaded successfully!")
    else:
        print("❌ Some models failed to load")
    return success

# ============================================================================
# ANALYSIS PIPELINE
# ============================================================================
def detect_objects(image_bytes):
    try:
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        results = models['yolo'](image, conf=HAND_CONFIDENCE_THRESHOLD)
        
        detections = []
        for result in results:
            if result.boxes is not None:
                for box in result.boxes:
                    class_id = int(box.cls)
                    confidence = float(box.conf)
                    class_name = models['yolo'].names[class_id]
                    if class_name in TARGET_CLASSES:
                        detections.append({
                            'class': class_name,
                            'confidence': confidence
                        })
        
        detections.sort(key=lambda x: x['confidence'], reverse=True)
        return detections[0] if detections else None
        
    except Exception as e:
        print(f"❌ Detection error: {e}")
        return None

def analyze_with_llava(image_bytes):
    try:
        print("🔄 Starting LLaVA image analysis...")
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        
        conversation = [{
            "role": "user",
            "content": [
                {"type": "image"},
                {"type": "text", "text": MEDICAL_IMAGE_ANALYSIS_PROMPT},
            ],
        }]
        
        text_prompt = models['vision_processor'].apply_chat_template(conversation, add_generation_prompt=True)
        inputs = models['vision_processor'](image, text_prompt, return_tensors="pt").to(models['vision_model'].device)
        
        print("🔄 LLaVA generating analysis...")
        with torch.no_grad():
            output = models['vision_model'].generate(
                **inputs,
                max_new_tokens=400,
                do_sample=False,
                temperature=0.1
            )
        
        response = models['vision_processor'].decode(output[0], skip_special_tokens=True)
        assistant_start = response.find("[/INST]") + len("[/INST]")
        if assistant_start > len("[/INST]") - 1:
            analysis = response[assistant_start:].strip()
        else:
            analysis = response
            
        print("✅ LLaVA analysis completed!")
        print("=" * 60)
        print("👁️ LLAVA MEDICAL IMAGE ANALYSIS:")
        print("=" * 60)
        print(analysis)
        print("=" * 60)
        
        return analysis
        
    except Exception as e:
        print(f"❌ LLaVA analysis error: {e}")
        return None

def generate_clinical_text(prompt, max_tokens=500):
    try:
        inputs = models['clinical_tokenizer'](
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=1500,
            padding=False
        )
        
        device = next(models['clinical_model'].parameters()).device
        inputs = {k: v.to(device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = models['clinical_model'].generate(
                **inputs,
                max_new_tokens=max_tokens,
                temperature=0.2,
                do_sample=True,
                repetition_penalty=1.1,
                pad_token_id=models['clinical_tokenizer'].pad_token_id,
                eos_token_id=models['clinical_tokenizer'].eos_token_id
            )
        
        generated_text = models['clinical_tokenizer'].decode(outputs[0], skip_special_tokens=True)
        return generated_text[len(prompt):].strip()
        
    except Exception as e:
        print(f"❌ Clinical generation error: {e}")
        return None

def run_medical_pipeline(image_bytes):
    """
    COMPLETE PIPELINE: Image → YOLO → LLaVA → Combine → Summarizer → Diagnoser → Questioner
    """
    
    # Step 1: Object Detection
    print("🔍 Step 1: Object Detection")
    detection = detect_objects(image_bytes)
    if not detection:
        return {"error": "No relevant objects detected"}
    print(f"✅ Detected: {detection['class']} ({detection['confidence']:.1%})")
    
    # Step 2: LLaVA Analysis
    print("🔍 Step 2: LLaVA Analysis")
    llava_analysis = analyze_with_llava(image_bytes)
    if not llava_analysis:
        return {"error": "LLaVA analysis failed"}
    
    # Step 3: Combine with base patient info
    print("🔍 Step 3: Combining patient information")
    combined_patient_info = f"""{BASE_PATIENT_INFO}

Medical Image Analysis: {llava_analysis}"""
    
    print("📋 Combined Patient Info:")
    print("-" * 40)
    print(combined_patient_info)
    print("-" * 40)
    
    # Step 4: Clinical Summary Generation
    print("🔍 Step 4: Clinical Summarizer")
    summary_prompt = f"""You are a clinical summarizer. Given the following patient information, extract and summarize the key clinical findings into a structured clinical vignette.

Patient Information:
{combined_patient_info}

Clinical Summary:"""
    
    clinical_summary = generate_clinical_text(summary_prompt, max_tokens=400)
    if not clinical_summary:
        return {"error": "Clinical summary failed"}
    
    print("📋 Clinical Summary:")
    print("-" * 40)
    print(clinical_summary)
    print("-" * 40)
    
    # Step 5: Diagnostic Reasoning
    print("🔍 Step 5: Diagnostic Reasoning")
    diagnostic_prompt = f"""You are a diagnostic reasoning model. Based on the clinical summary, generate a list of plausible diagnoses with reasoning.

Clinical Summary:
{clinical_summary}

Diagnostic Analysis:"""
    
    diagnostic_analysis = generate_clinical_text(diagnostic_prompt, max_tokens=400)
    if not diagnostic_analysis:
        return {"error": "Diagnostic analysis failed"}
    
    print("🔬 Diagnostic Analysis:")
    print("-" * 40)
    print(diagnostic_analysis)
    print("-" * 40)
    
    # Step 6: Question Generation
    print("🔍 Step 6: Question Generation")
    question_prompt = f"""You are a medical questioning agent. Based on the clinical summary and diagnostic analysis, generate ONE specific, relevant medical question to gather more information for diagnosis.

Clinical Summary:
{clinical_summary}

Diagnostic Analysis:
{diagnostic_analysis}

Generate ONE clear, specific medical question:"""
    
    medical_question = generate_clinical_text(question_prompt, max_tokens=200)
    if not medical_question:
        return {"error": "Question generation failed"}
    
    # Clean up the question
    medical_question = medical_question.split('\n')[0].strip()
    if not medical_question.endswith('?'):
        medical_question += '?'
    
    print("❓ Generated Medical Question:")
    print("=" * 60)
    print(f"🩺 {medical_question}")
    print("=" * 60)
    
    return {
        "success": True,
        "detection": detection,
        "llava_analysis": llava_analysis,
        "combined_patient_info": combined_patient_info,
        "clinical_summary": clinical_summary,
        "diagnostic_analysis": diagnostic_analysis,
        "medical_question": medical_question,
        "timestamp": datetime.now().isoformat()
    }

# ============================================================================
# FLASK ROUTES
# ============================================================================
@app.route("/")
def home():
    return jsonify({
        "status": "online",
        "message": "Complete Medical Analysis Server",
        "models_loaded": all(model is not None for model in models.values()),
        "gpu_available": torch.cuda.is_available()
    })

@app.route("/quick_detect", methods=["POST"])
def quick_detect():
    """Quick YOLO detection only - no LLaVA analysis"""
    try:
        if 'image' not in request.files:
            return jsonify({"error": "No image provided"}), 400
            
        image_file = request.files['image']
        image_bytes = image_file.read()
        
        print(f"🔍 Quick detection check for {len(image_bytes)} byte image")
        
        # Only run YOLO detection
        detection = detect_objects(image_bytes)
        
        if detection:
            print(f"✅ Quick detect: {detection['class']} ({detection['confidence']:.1%})")
            return jsonify({
                "detected": True,
                "detection": detection
            })
        else:
            print("❌ Quick detect: No objects found")
            return jsonify({
                "detected": False
            })
            
    except Exception as e:
        print(f"❌ Quick detection error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/analyze_frame", methods=["POST"])
def analyze_frame():
    """
    COMPLETE PIPELINE: Image → YOLO → LLaVA → Summary → Diagnosis → Question
    """
    try:
        if 'image' not in request.files:
            return jsonify({"error": "No image provided"}), 400
            
        image_file = request.files['image']
        image_bytes = image_file.read()
        
        print(f"\n🚀 Starting COMPLETE medical pipeline for {len(image_bytes)} byte image")
        print("=" * 80)
        
        # Run the complete pipeline
        result = run_medical_pipeline(image_bytes)
        
        if "error" in result:
            print(f"❌ Pipeline failed: {result['error']}")
            return jsonify(result), 500
        
        print("✅ Complete medical pipeline finished successfully!")
        print("=" * 80)
        return jsonify(result)
        
    except Exception as e:
        print(f"❌ Pipeline error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "healthy",
        "models_loaded": {
            "yolo": models['yolo'] is not None,
            "llava": models['vision_model'] is not None,
            "clinical": models['clinical_model'] is not None
        },
        "gpu_available": torch.cuda.is_available(),
        "timestamp": datetime.now().isoformat()
    })

# ============================================================================
# MAIN EXECUTION
# ============================================================================
def main():
    print("🏥 Complete Medical Analysis Server")
    print("=" * 50)
    print("📋 Pipeline: Image → YOLO → LLaVA → Summary → Diagnosis → Question")
    print(f"🔍 YOLO Detection Threshold: {HAND_CONFIDENCE_THRESHOLD}")
    print(f"🎯 Target Classes: {TARGET_CLASSES}")
    print(f"🎮 GPU Available: {torch.cuda.is_available()}")
    
    if torch.cuda.is_available():
        print(f"🔧 GPU Count: {torch.cuda.device_count()}")
        for i in range(torch.cuda.device_count()):
            props = torch.cuda.get_device_properties(i)
            print(f"💾 GPU {i}: {props.name} ({props.total_memory / 1e9:.1f} GB)")
    
    if not initialize_models():
        print("❌ Failed to initialize models - exiting")
        return
    
    print("\n🌐 Starting Flask server...")
    print("📋 Endpoints:")
    print("  GET  /          - Server status")
    print("  POST /quick_detect - Fast YOLO detection only")
    print("  POST /analyze_frame - Complete medical pipeline")
    print("  GET  /health    - Health check")
    print("\n🚀 Server ready!")
    
    app.run(host="0.0.0.0", port=7860, debug=False, threaded=True)

if __name__ == "__main__":
    main()
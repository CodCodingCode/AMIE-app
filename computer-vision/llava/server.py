import torch
from transformers import LlavaNextProcessor, LlavaNextForConditionalGeneration
from PIL import Image
import requests
from flask import Flask, request, jsonify
import io

app = Flask(__name__)

MODEL_NAME = "llava-hf/llava-v1.6-mistral-7b-hf"
print("🔄 Loading LLaVA-NeXT model...")
processor = LlavaNextProcessor.from_pretrained(MODEL_NAME)
model = LlavaNextForConditionalGeneration.from_pretrained(
    MODEL_NAME,
    torch_dtype=torch.float16,
    device_map="auto"
)
processor.tokenizer.padding_side = "left"
print("✅ Model loaded successfully!")

GENERAL_MEDICAL_IMAGE_PROMPT = """
You are an AI-powered medical assistant. Given the attached photo of a patient’s body part, object, or condition, analyze the image carefully and provide a detailed, medically relevant description that can assist a healthcare provider in understanding what is depicted.

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

@app.route("/")
def home():
    return "✅ LLaVA-NeXT Server is Running!"

@app.route("/analyze_url", methods=["POST"])
def analyze_url():
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

# <-- NEW endpoint for direct image upload
@app.route("/analyze_image", methods=["POST"])
def analyze_image():
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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7860)
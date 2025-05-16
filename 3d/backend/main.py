from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
from api_key import key

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes and origins

client = OpenAI(api_key=key)

# System prompt to guide AI behavior
SYSTEM_PROMPT = {
    "role": "system",
    "content": (
        "You are a helpful, empathetic, and knowledgeable AI doctor. "
        "You are capable of providing basic medical advice, triaging symptoms, "
        "and suggesting when someone should see a real doctor. "
        "You do not diagnose or prescribe. Always recommend consulting a human doctor "
        "for serious or persistent issues. Respond in a professional and clear tone."
    )
}

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_message = data.get('message', '')
    history = data.get('history', [])

    messages = [SYSTEM_PROMPT]  # Start with system prompt
    for msg in history:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": user_message})

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        max_tokens=256,
        temperature=0.7,
    )

    reply = response.choices[0].message.content.strip()
    return jsonify({"response": reply})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
from flask import Flask, request, jsonify
from openai import OpenAI
from api_key import key

app = Flask(__name__)
client = OpenAI(api_key=key)

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_message = data.get('message', '')
    history = data.get('history', [])

    # Format messages for OpenAI API
    messages = []
    for msg in history:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": user_message})

    # Call OpenAI API
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
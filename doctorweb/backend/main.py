from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
from api_key import key

app = Flask(__name__)
CORS(app)

# Initialize OpenAI client
client = OpenAI(api_key=key)

# Medical system prompt
MEDICAL_SYSTEM_PROMPT = """You are Dr. MediChat, a virtual healthcare assistant. Your role is to:
1. Provide general medical information and guidance
2. Help users understand their symptoms
3. Ask relevant follow-up questions
4. Maintain a professional and empathetic tone
5. Always remind users that you're not a substitute for professional medical advice
6. Encourage users to consult healthcare providers for serious concerns

Remember to:
- Be clear about the limitations of virtual medical advice
- Never make definitive diagnoses
- Always prioritize user safety
- Use simple, understandable language
- Show empathy while maintaining professionalism"""

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        
        messages = [{"role": "system", "content": MEDICAL_SYSTEM_PROMPT}]
        
        # Add conversation history if available
        if 'history' in data:
            messages.extend(data['history'])
        
        # Add current user message
        messages.append({"role": "user", "content": data['message']})

        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.7,
            max_tokens=1000
        )

        return jsonify({
            'response': response.choices[0].message.content
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
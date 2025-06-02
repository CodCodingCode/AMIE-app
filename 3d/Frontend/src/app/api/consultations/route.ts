// app/api/consultations/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { OpenAI } from 'openai';

// Initialize OpenAI client
const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY
});

// Helper function to clean JSON response from GPT
function cleanJsonResponse(content: string): string {
  let cleaned = content.trim();
  if (cleaned.startsWith('```json')) {
    cleaned = cleaned.replace(/^```json\s*/, '');
  }
  if (cleaned.startsWith('```')) {
    cleaned = cleaned.replace(/^```\s*/, '');
  }
  if (cleaned.endsWith('```')) {
    cleaned = cleaned.replace(/\s*```$/, '');
  }
  return cleaned.trim();
}

// GPT-powered SOAP Note generation
async function generateSOAPNote(chatId: string, messages: any[]) {
  const conversationText = messages.map(msg => 
    `${msg.sender === 'user' ? 'Patient' : 'AI Doctor'}: ${msg.text}`
  ).join('\n\n');

  const soapPrompt = `Based on the following patient consultation, generate a professional SOAP note. You must respond with ONLY a valid JSON object, no markdown formatting, no explanations, no code blocks.

Conversation:
${conversationText}

Generate a JSON object with exactly these fields:
- "subjective": string - Patient's reported symptoms and concerns
- "objective": string - Note this was a virtual consultation with no physical exam
- "assessment": string - Clinical assessment based on the conversation  
- "plan": array of strings - Recommended next steps and treatments

Respond with only the JSON object, nothing else.`;

  const response = await openai.chat.completions.create({
    model: "gpt-4o-mini",
    messages: [
      { 
        role: 'system', 
        content: 'You are a medical professional. Respond only with valid JSON. Never use markdown formatting or code blocks. Always return a plain JSON object.' 
      },
      { role: 'user', content: soapPrompt }
    ],
    temperature: 0.3,
    max_tokens: 1000
  });

  const content = response.choices[0]?.message?.content || '';
  const cleanedContent = cleanJsonResponse(content);
  
  try {
    const parsedSoap = JSON.parse(cleanedContent);
    return {
      chatId: chatId,
      generatedAt: new Date().toISOString(),
      ...parsedSoap
    };
  } catch (error) {
    console.error('Failed to parse SOAP JSON:', cleanedContent);
    return {
      chatId: chatId,
      generatedAt: new Date().toISOString(),
      subjective: "Patient consultation documented. Detailed symptoms and concerns as reported during virtual visit.",
      objective: "Virtual consultation conducted. No physical examination performed. Patient appeared alert and responsive during video call.",
      assessment: "Assessment based on patient-reported symptoms and virtual consultation. Further in-person evaluation may be warranted.",
      plan: [
        "Continue monitoring symptoms",
        "Follow up with healthcare provider as needed", 
        "Seek immediate medical attention if symptoms worsen"
      ]
    };
  }
}

// GPT-powered Referral generation
async function generateReferral(chatData: any) { // chatData contains id, userId, title, messages etc.
  const conversationText = chatData.messages.map((msg: any) => 
    `${msg.sender === 'user' ? 'Patient' : 'AI Doctor'}: ${msg.text}`
  ).join('\n\n');

  const referralPrompt = `Based on the following patient consultation, generate a medical referral. You must respond with ONLY a valid JSON object, no markdown formatting, no explanations, no code blocks.

Conversation:
${conversationText}

Generate a JSON object with exactly these fields:
- "referralTo": string - What type of specialist or specific doctor should see this patient
- "urgency": string - Must be one of: "routine", "urgent"
- "reason": string - Brief reason for referral
- "symptoms": array of strings - Key symptoms mentioned
- "clinicalSummary": string - 2-3 sentence summary for the specialist

Respond with only the JSON object, nothing else.`;

  const response = await openai.chat.completions.create({
    model: "gpt-4o-mini",
    messages: [
      { 
        role: 'system', 
        content: 'You are a medical professional. Respond only with valid JSON. Never use markdown formatting or code blocks. Always return a plain JSON object. Ensure urgency is one of "routine" or "urgent".' 
      },
      { role: 'user', content: referralPrompt }
    ],
    temperature: 0.3,
    max_tokens: 800
  });

  const content = response.choices[0]?.message?.content || '';
  const cleanedContent = cleanJsonResponse(content);
  
  try {
    const referralDetails = JSON.parse(cleanedContent);
    // Ensure urgency is valid, default to routine if not
    if (!['routine', 'urgent'].includes(referralDetails.urgency)) {
        referralDetails.urgency = 'routine';
    }
    return {
      chatId: chatData.id, // Corresponds to ConsultationId
      patientId: chatData.userId,
      createdAt: new Date().toISOString(), // Corresponds to referralDate
      status: 'pending', // Default status
      ...referralDetails // contains referralTo, urgency, reason, symptoms, clinicalSummary
    };
  } catch (error) {
    console.error('Failed to parse Referral JSON:', cleanedContent);
    return {
      chatId: chatData.id,
      patientId: chatData.userId,
      createdAt: new Date().toISOString(),
      referralTo: "General Medicine",
      urgency: "routine",
      reason: chatData.title || "Follow-up required",
      symptoms: ["As reported in consultation"],
      clinicalSummary: "Patient consultation completed via virtual visit. Requires in-person evaluation and assessment.",
      status: 'pending'
    };
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { action, chatData } = body;

    if (!chatData || !chatData.id || !chatData.messages) {
      return NextResponse.json({ error: 'Valid chat data (including id and messages) is required' }, { status: 400 });
    }

    switch (action) {
      case 'generateSOAP':
        const soapNote = await generateSOAPNote(chatData.id, chatData.messages);
        return NextResponse.json({ success: true, soapNote: soapNote });

      case 'referToDoctor': // Frontend uses this action name
        const referral = await generateReferral(chatData);
        return NextResponse.json({ success: true, referral: referral });

      default:
        return NextResponse.json({ error: 'Invalid action' }, { status: 400 });
    }
  } catch (error) {
    console.error('API error:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}
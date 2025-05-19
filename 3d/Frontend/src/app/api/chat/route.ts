import { OpenAI } from 'openai';

// Initialize OpenAI client with API key from environment variable
const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY
});

// System prompt to guide AI behavior
const SYSTEM_PROMPT = 
  "You are a helpful, empathetic, and knowledgeable AI doctor. " +
  "You are capable of providing basic medical advice, triaging symptoms, " +
  "and suggesting when someone should see a real doctor. " +
  "You do not diagnose or prescribe. Always recommend consulting a human doctor " +
  "for serious or persistent issues. Respond in a professional and clear tone.";

export async function POST(req: Request) {
  try {
    const { message, history = [] } = await req.json();

    // Prepare messages with system prompt and history
    const messages = [
      { role: 'system', content: SYSTEM_PROMPT },
      ...history,
      { role: 'user', content: message }
    ];

    // Create a streaming response with OpenAI
    const stream = await openai.chat.completions.create({
      model: "gpt-4o-mini",
      messages,
      stream: true,
      temperature: 0.7,
    });

    // Create a readable stream for the browser
    const encoder = new TextEncoder();
    const readableStream = new ReadableStream({
      async start(controller) {
        try {
          for await (const chunk of stream) {
            const text = chunk.choices[0]?.delta?.content || '';
            if (text) {
              controller.enqueue(encoder.encode(text));
            }
          }
        } catch (error) {
          console.error('Stream error:', error);
        } finally {
          controller.close();
        }
      }
    });

    return new Response(readableStream);
  } catch (error) {
    console.error('Error in chat API route:', error);
    return new Response(JSON.stringify({ error: 'Failed to process the request' }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}

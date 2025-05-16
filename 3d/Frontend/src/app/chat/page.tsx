'use client';

import React, { useState, useRef, useEffect } from 'react';

interface Message {
  text: string;
  sender: 'user' | 'assistant';
}

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [isFirstMessage, setIsFirstMessage] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const chatHistoryRef = useRef<Array<{role: string, content: string}>>([]);

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim() === '') return;

    const userMessage: Message = { text: input.trim(), sender: 'user' };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    
    // Add to chat history
    const messageObj = {
      role: "user",
      content: userMessage.text
    };
    chatHistoryRef.current.push(messageObj);
    
    // Set first message to false to transition UI
    if (isFirstMessage) {
      setIsFirstMessage(false);
    }
    
    setIsTyping(true);

    try {
      // Connect to Flask backend
      const response = await fetch('http://localhost:5001/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          message: userMessage.text,
          history: chatHistoryRef.current.slice(0, -1) // Send history without current message
        }),
      });

      setIsTyping(false);

      if (!response.ok) {
        throw new Error('Network response was not ok');
      }

      const data = await response.json();
      const assistantMessage: Message = { 
        text: data.response, 
        sender: 'assistant' 
      };
      
      setMessages(prev => [...prev, assistantMessage]);
      
      // Add to chat history
      chatHistoryRef.current.push({
        role: "assistant",
        content: data.response
      });
    } catch (error) {
      console.error('Error:', error);
      setIsTyping(false);
      setMessages(prev => [
        ...prev, 
        { 
          text: 'Sorry, I encountered an error. Please try again later.', 
          sender: 'assistant' 
        }
      ]);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-[#faf9f6]">
      <header className="text-center py-6">
        <h1 className="text-3xl font-semibold text-[#444444]">AI Doctor</h1>
      </header>
      
      <div className="flex-1 flex flex-col max-w-4xl mx-auto w-full px-4 relative">
        {/* Welcome Screen - visible when no messages */}
        {isFirstMessage && (
          <div className={`welcome-container flex flex-col items-center justify-center h-full text-center transition-opacity duration-500 ${!isFirstMessage ? 'opacity-0' : 'opacity-100'}`}>
            <h2 className="text-3xl font-semibold mb-4 text-[#333333]">AI Doctor Assistant</h2>
            <p className="text-lg text-[#666666] max-w-lg">
              I can answer health questions, help you understand symptoms, and recommend when to see a doctor. How can I help you today?
            </p>
          </div>
        )}
        
        {/* Messages Container */}
        <div 
          ref={messagesContainerRef}
          className={`flex-1 overflow-y-auto py-4 ${isFirstMessage ? 'hidden' : 'block'}`}
        >
          {messages.map((message, i) => (
            <div
              key={i}
              className={`message flex mb-6 animate-fadeIn ${
                message.sender === 'user' 
                  ? 'justify-end' 
                  : 'justify-start'
              }`}
            >
              <div 
                className={`max-w-[80%] p-4 rounded-xl ${
                  message.sender === 'user'
                    ? 'bg-[#4A6FA5] text-white rounded-br-sm'
                    : 'bg-[#F0F2F5] text-[#333333] rounded-bl-sm'
                }`}
              >
                {message.text}
              </div>
            </div>
          ))}

          {isTyping && (
            <div className="flex justify-start mb-6">
              <div className="bg-[#F0F2F5] p-4 rounded-xl rounded-bl-sm">
                <div className="flex space-x-2">
                  <div className="w-2 h-2 rounded-full bg-[#888888] opacity-60 animate-bounce"></div>
                  <div className="w-2 h-2 rounded-full bg-[#888888] opacity-60 animate-bounce" style={{animationDelay: '0.2s'}}></div>
                  <div className="w-2 h-2 rounded-full bg-[#888888] opacity-60 animate-bounce" style={{animationDelay: '0.4s'}}></div>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input form */}
        <div className="py-6">
          <form
            onSubmit={handleSendMessage}
            className="flex bg-white border border-[#E0E0E0] rounded-xl p-1 shadow-sm focus-within:shadow-md transition-shadow duration-300"
          >
            <textarea
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  if (input.trim() !== '') handleSendMessage(e);
                }
              }}
              placeholder="Ask your health question..."
              className="flex-1 py-3 px-4 focus:outline-none text-gray-700 resize-none max-h-40"
              style={{ minHeight: '56px' }}
              rows={1}
            />
            <button 
              type="submit" 
              className="bg-[#4A6FA5] text-white rounded-lg p-2 m-1 w-10 h-10 flex items-center justify-center disabled:bg-[#CCCCCC] disabled:cursor-not-allowed"
              disabled={input.trim() === ''}
              aria-label="Send message"
            >
              <svg viewBox="0 0 24 24" fill="none" className="w-5 h-5" xmlns="http://www.w3.org/2000/svg">
                <path d="M22 2L11 13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                <path d="M22 2L15 22L11 13L2 9L22 2Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </button>
          </form>
        </div>
      </div>
      
      <footer className="text-center py-4 text-sm text-[#888888]">
        <p>AI Doctor is not a replacement for professional medical advice, diagnosis, or treatment.</p>
      </footer>
      
      <style jsx global>{`
        @keyframes fadeIn {
          from {
            opacity: 0;
            transform: translateY(10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        
        .animate-fadeIn {
          animation: fadeIn 0.5s ease-out forwards;
        }

        textarea {
          overflow-y: auto;
        }
      `}</style>
    </div>
  );
}
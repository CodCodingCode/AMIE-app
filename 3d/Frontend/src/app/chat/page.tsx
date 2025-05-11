'use client';
import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

// Mock user data to replace Firebase auth
interface MockUser {
  displayName: string;
  photoURL: string | null;
}

export default function Chat() {
  // Replace Firebase user with simple state
  const [user, setUser] = useState<MockUser>({ displayName: 'Guest User', photoURL: null });
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [conversationStarted, setConversationStarted] = useState(false);
  const [isInitialLoad, setIsInitialLoad] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const router = useRouter();

  // Check if conversation has already started
  useEffect(() => {
    setConversationStarted(messages.length > 0);
  }, [messages]);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Focus input on component mount and handle initial fade-in
  useEffect(() => {
    const timer = setTimeout(() => {
      inputRef.current?.focus();
      setIsInitialLoad(false);
    }, 1000);
    
    return () => clearTimeout(timer);
  }, []);

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;
    
    const messageToSend = inputMessage; // Store the message before clearing input
    setInputMessage(''); // Clear input field immediately before processing
    setIsLoading(true);

    // Add user message to local state
    setMessages(prev => [...prev, { role: 'user', content: messageToSend }]);

    // Send to backend API
    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: messageToSend,
          history: messages
        }),
      });
      
      const data = await response.json();

      // Add assistant message to local state
      setMessages(prev => [...prev, { role: 'assistant', content: data.response }]);
    } catch (error) {
      console.error('Error sending message:', error);
      // Fallback response if API call fails
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: "I'm sorry, I'm having trouble connecting to the server. Please try again later." 
      }]);
    }

    setIsLoading(false);
  };

  return (
    <div className="flex flex-col h-screen bg-slate-50">
      {/* Claude-like interface when no conversation started */}
      {!conversationStarted ? (
        <motion.div 
          className="flex flex-col items-center justify-center h-full w-full px-4"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.6 }}
        >
          {/* User greeting with proper profile image */}
          <motion.div 
            className="mb-8 text-center"
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.2, duration: 0.5 }}
          >
            <div className="flex items-center justify-center mb-3">
              <div className="w-12 h-12 rounded-full bg-blue-100 flex items-center justify-center overflow-hidden">
                {user?.photoURL ? (
                  <img 
                    src={user.photoURL} 
                    alt="User" 
                    className="w-full h-full object-cover"
                    referrerPolicy="no-referrer"
                  />
                ) : (
                  <span className="text-blue-600 font-semibold">{user?.displayName?.charAt(0) || "U"}</span>
                )}
              </div>
            </div>
            <h2 className="text-2xl font-medium text-gray-800">
              Welcome to AI Doctor Chat!
            </h2>
          </motion.div>

          {/* Main chat input - centered like Claude */}
          <motion.div 
            className="w-full max-w-xl bg-white rounded-xl shadow-lg overflow-hidden"
            initial={{ y: 20, opacity: 0, scale: 0.95 }}
            animate={{ y: 0, opacity: 1, scale: 1 }}
            transition={{ delay: 0.4, duration: 0.5 }}
          >
            <div className="px-4 py-4 border-b border-gray-100">
              <h3 className="text-lg font-semibold text-gray-800 text-center">Chat with your AI Doctor</h3>
            </div>
            <div className="p-4">
              <textarea
                ref={inputRef as any}
                className="w-full p-4 border-none outline-none bg-gray-50 rounded-lg text-gray-800 resize-none min-h-[120px]"
                placeholder="How can I help you today?"
                value={inputMessage}
                onChange={e => setInputMessage(e.target.value)}
                onKeyDown={e => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSendMessage();
                  }
                }}
              />
              <div className="flex justify-between items-center mt-4">
                <div className="text-sm text-gray-500">AI Doctor at your service</div>
                <button
                  onClick={handleSendMessage}
                  disabled={isLoading || !inputMessage.trim()}
                  className={`
                    px-4 py-2 rounded-lg
                    ${inputMessage.trim() ? 'bg-blue-600 hover:bg-blue-700' : 'bg-gray-300'} 
                    text-white transition-all duration-200
                    disabled:opacity-50 disabled:cursor-not-allowed
                  `}
                >
                  Send
                </button>
              </div>
            </div>
          </motion.div>

        </motion.div>
      ) : (
        
        // Regular chat interface once conversation has started
        <div className="flex-1 flex flex-col w-full h-full">
          {/* Header - always visible, centered */}
          <div className="py-6 text-center animate-fade-in bg-white shadow-sm z-10">
            <h1 className="text-2xl font-bold text-blue-800">
              Chat to your personal AI Doctor today.
            </h1>
          </div>

          {/* Messages area - full width and height */}
          <div className="flex-1 flex items-center justify-center overflow-hidden">
            <div className="w-full max-w-4xl flex flex-col h-full">
              {/* Added custom scrollbar styling to hide the scrollbar but keep functionality */}
              <div className="flex-1 overflow-y-auto p-6 scrollbar-hide">
                <div className="space-y-4">
                  {messages.map((msg, idx) => (
                    <div
                      key={idx}
                      className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} animate-fadeIn`}
                    >
                      <div className={`
                        max-w-[80%] rounded-xl p-3.5 
                        ${msg.role === 'user' 
                          ? 'bg-blue-500 text-white' 
                          : 'bg-gray-100 text-gray-800'}
                        transform transition-all duration-300 ease-out
                      `}
                      style={{
                        animation: `fadeSlide${msg.role === 'user' ? 'Left' : 'Right'} 0.3s ease-out forwards`
                      }}
                      >
                        {msg.role === 'assistant' && (
                          <div className="flex items-center mb-1">
                            <div className="w-6 h-6 rounded-full bg-purple-600 flex items-center justify-center mr-2">
                              <span className="text-white text-xs">AI</span>
                            </div>
                            <span className="text-xs font-medium text-gray-500">Assistant</span>
                          </div>
                        )}
                        {msg.role === 'user' && (
                          <div className="flex items-center justify-end mb-1">
                            <span className="text-xs font-medium text-blue-200">You</span>
                            {user?.photoURL ? (
                              <img 
                                src={user.photoURL} 
                                alt="Profile" 
                                className="w-6 h-6 rounded-full ml-2 object-cover" 
                                referrerPolicy="no-referrer"
                              />
                            ) : (
                              <div className="w-6 h-6 rounded-full bg-blue-600 flex items-center justify-center ml-2">
                                <span className="text-white text-xs">{user?.displayName?.charAt(0) || "U"}</span>
                              </div>
                            )}
                          </div>
                        )}
                        <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                      </div>
                    </div>
                  ))}
                  
                  {isLoading && (
                    <div className="flex justify-start animate-fadeIn">
                      <div className="bg-gray-100 text-gray-800 rounded-xl p-3.5 transform transition-all duration-300 ease-out"
                        style={{ animation: 'fadeSlideRight 0.3s ease-out forwards' }}>
                        <div className="flex items-center mb-1">
                          <div className="w-6 h-6 rounded-full bg-purple-600 flex items-center justify-center mr-2">
                            <span className="text-white text-xs">AI</span>
                          </div>
                          <span className="text-xs font-medium text-gray-500">Assistant</span>
                        </div>
                        <div className="flex space-x-2 px-2 py-1">
                          <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce"></div>
                          <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                          <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></div>
                        </div>
                      </div>
                    </div>
                  )}
                  <div ref={messagesEndRef} />
                </div>
              </div>
            </div>
          </div>
          
          {/* Input area */}
          <div className="p-4 bg-white border-t border-gray-100 shadow-inner">
            <div className="max-w-4xl mx-auto transition-all duration-500">
              <div className="flex items-center space-x-2">
                <input
                  type="text"
                  className="flex-1 border border-gray-300 rounded-full px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 text-black"
                  placeholder="Message your AI Doctor..."
                  value={inputMessage}
                  onChange={e => setInputMessage(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && handleSendMessage()}
                  disabled={isLoading}
                />
                <button
                  onClick={handleSendMessage}
                  disabled={isLoading || !inputMessage.trim()}
                  className={`
                    rounded-full p-3
                    ${inputMessage.trim() ? 'bg-blue-600 hover:bg-blue-700' : 'bg-gray-300'} 
                    text-white transition-all duration-200 transform hover:scale-105 
                    disabled:opacity-50 disabled:cursor-not-allowed
                    shadow-md hover:shadow-lg
                  `}
                >
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                    <path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.428a1 1 0 001.17-1.408l-7-14z" />
                  </svg>
                </button>
              </div>
              <p className="text-xs text-center text-gray-500 mt-2">
                AI Doctor is here to assist with health-related questions.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Add CSS to hide scrollbars */}
      <style jsx global>{`
        /* Hide scrollbar for Chrome, Safari and Opera */
        .scrollbar-hide::-webkit-scrollbar {
          display: none;
        }
        
        /* Hide scrollbar for IE, Edge and Firefox */
        .scrollbar-hide {
          -ms-overflow-style: none;  /* IE and Edge */
          scrollbar-width: none;  /* Firefox */
        }
      `}</style>
    </div>
  );
}
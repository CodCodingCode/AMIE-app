'use client';
import { useEffect, useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { auth, db } from "../firebase";
import { onAuthStateChanged, User } from "firebase/auth";
import { collection, addDoc, query, orderBy, onSnapshot, serverTimestamp } from "firebase/firestore";
import Image from "next/image";
import { Inter } from "next/font/google";

// Using Inter as a modern, clean font
const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: any; // Firestore timestamp
}

export default function Chat() {
  const [user, setUser] = useState<User | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const router = useRouter();

  // Auth state
  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (firebaseUser) => {
      if (!firebaseUser) {
        router.push("/");
      } else {
        setUser(firebaseUser);
      }
    });
    return () => unsubscribe();
  }, [router]);

  // Firestore listener
  useEffect(() => {
    if (!user) return;
    const q = query(
      collection(db, "users", user.uid, "chats", "default", "messages"),
      orderBy("timestamp")
    );
    const unsubscribe = onSnapshot(q, (querySnapshot) => {
      const loadedMessages = querySnapshot.docs.map(doc => doc.data() as Message);
      setMessages(loadedMessages);
    });
    return () => unsubscribe();
  }, [user]);

  // Scroll to bottom on new message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isLoading || !user) return;
    
    setIsLoading(true);
    const userMessage = {
      role: 'user',
      content: inputMessage,
      timestamp: serverTimestamp()
    };

    await addDoc(
      collection(db, "users", user.uid, "chats", "default", "messages"),
      userMessage
    );

    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: inputMessage,
        history: messages.map(msg => ({
          role: msg.role,
          content: msg.content
        }))
      }),
    });

    const data = await response.json();
    
    await addDoc(
      collection(db, "users", user.uid, "chats", "default", "messages"),
      {
        role: 'assistant',
        content: data.response,
        timestamp: serverTimestamp()
      }
    );

    setInputMessage('');
    setIsLoading(false);
  };

  if (!user) return null;

  return (
    <div className={`flex flex-col h-screen bg-gradient-to-br from-blue-50 to-white text-gray-800 ${inter.variable} font-sans`}>
      {/* Header */}
      <header className="flex items-center justify-between px-6 py-4 bg-gradient-to-r from-blue-600 to-blue-500 text-white backdrop-blur-sm shadow-lg">
        <div className="flex items-center gap-3">
          <div className="relative w-8 h-8">
            <Image
              src="/favicon.ico"
              alt="Bluebox Logo"
              fill
              priority
              className="object-contain"
            />
          </div>
          <h1 className="font-light text-xl tracking-wide">Medi<span className="font-bold">Chat</span></h1>
        </div>
        <button 
          onClick={() => auth.signOut()}
          className="rounded-full bg-white bg-opacity-20 hover:bg-opacity-30 p-2 transition-all duration-300"
        >
          Sign Out
        </button>
      </header>

      {/* Main content */}
      <main className="flex flex-1 overflow-hidden">
        {/* Chat area */}
        <div className="flex-1 flex flex-col bg-gradient-to-br from-white to-blue-50">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto px-4 md:px-6 pb-4 space-y-6">
            {messages.map((message, index) => (
              <div 
                key={index} 
                className={`flex items-start gap-3 max-w-2xl ${message.role === 'user' ? 'ml-auto' : ''}`}
              >
                {message.role === 'assistant' && (
                  <div className="shrink-0 w-10 h-10 rounded-full bg-blue-100 border-2 border-white shadow-sm flex items-center justify-center">
                    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"></path>
                    </svg>
                  </div>
                )}
                <div className={`${
                  message.role === 'user' 
                    ? 'bg-gradient-to-r from-blue-600 to-blue-500 text-white rounded-2xl rounded-tr-none' 
                    : 'bg-white rounded-2xl rounded-tl-none border border-blue-100'
                } p-4 shadow-sm space-y-2`}>
                  {message.role === 'assistant' && (
                    <p className="text-blue-700 font-medium text-sm">Doctor Bluebox</p>
                  )}
                  <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
                </div>
                {message.role === 'user' && (
                  <div className="shrink-0 w-10 h-10 rounded-full bg-gray-200 border-2 border-white shadow-sm flex items-center justify-center">
                    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                      <circle cx="12" cy="7" r="4"></circle>
                    </svg>
                  </div>
                )}
              </div>
            ))}
            {isLoading && (
              <div className="flex items-start gap-3 max-w-2xl">
                <div className="shrink-0 w-10 h-10 rounded-full bg-blue-100 border-2 border-white shadow-sm flex items-center justify-center">
                  <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"></path>
                  </svg>
                </div>
                <div className="bg-white p-4 rounded-2xl rounded-tl-none shadow-sm border border-blue-100">
                  <div className="flex space-x-2">
                    <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                    <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></div>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Message input */}
          <div className="border-t border-blue-100 bg-white bg-opacity-70 backdrop-blur-sm p-4">
            <div className="flex items-center gap-3 max-w-4xl mx-auto">
              <div className="flex-1 flex items-center bg-white rounded-xl px-4 py-3 border border-blue-100 shadow-sm">
                <input 
                  type="text" 
                  placeholder="Type your health question..." 
                  className="flex-1 bg-transparent outline-none text-sm"
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                  disabled={isLoading}
                />
                <button 
                  onClick={handleSendMessage}
                  disabled={isLoading}
                  className="ml-1 bg-gradient-to-r from-blue-600 to-blue-500 hover:from-blue-700 hover:to-blue-600 text-white p-2 rounded-xl transition-all shadow-sm hover:shadow-md disabled:opacity-50"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                    <line x1="22" y1="2" x2="11" y2="13"></line>
                    <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
                  </svg>
                </button>
              </div>
            </div>
            <div className="mt-2 text-center">
              <span className="text-xs text-gray-400">Remember: This is not a substitute for professional medical advice, diagnosis, or treatment.</span>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
} 
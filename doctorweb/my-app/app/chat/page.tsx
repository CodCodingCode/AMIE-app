'use client';
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { auth, provider } from "../firebase";
import { signInWithPopup, onAuthStateChanged, User } from "firebase/auth";
import Image from "next/image";
import { Inter } from "next/font/google";

// Using Inter as a modern, clean font
const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });

export default function ChatPage() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (firebaseUser) => {
      setUser(firebaseUser);
      setLoading(false);
    });
    return () => unsubscribe();
  }, []);

  const signInWithGoogle = async () => {
    try {
      await signInWithPopup(auth, provider);
    } catch (err) {
      alert("Sign in failed. Please try again.");
    }
  };

  if (loading) {
    return <div className="flex items-center justify-center h-screen text-blue-600 text-xl">Loading...</div>;
  }

  if (!user) {
    // Not signed in: show sign-in prompt
    return (
      <div className={`min-h-screen flex flex-col items-center justify-center ${inter.variable} font-sans bg-gradient-to-br from-white to-blue-50`}>
        <main className="flex flex-col items-center justify-center flex-1 w-full text-center">
          <h1 className="text-4xl font-bold mb-6 text-gray-900">Sign in to access MediChat</h1>
          <button
            onClick={signInWithGoogle}
            className="rounded-full bg-blue-600 hover:bg-blue-700 text-white px-10 py-4 font-semibold text-xl shadow-lg transition mb-8"
          >
            Sign in with Google
          </button>
          <button
            onClick={() => router.push("/")}
            className="text-blue-600 underline"
          >
            Back to Home
          </button>
        </main>
      </div>
    );
  }

  // Signed in: show chat UI
  return (
    <div className={`flex flex-col h-screen bg-gradient-to-br from-blue-50 to-white text-gray-800 ${inter.variable} font-sans`}>
      {/* Header */}
      <header className="flex items-center justify-between px-6 py-4 bg-gradient-to-r from-blue-600 to-blue-500 text-white backdrop-blur-sm shadow-lg">
        <div className="flex items-center gap-3">
          <div className="relative w-8 h-8">
            <Image
              src="/medical-logo.svg"
              alt="MediChat Logo"
              fill
              priority
              className="object-contain"
            />
          </div>
          <h1 className="font-light text-xl tracking-wide">Medi<span className="font-bold">Chat</span></h1>
        </div>
        <button className="rounded-full bg-white bg-opacity-20 hover:bg-opacity-30 p-2 transition-all duration-300">
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="1"></circle>
            <circle cx="19" cy="12" r="1"></circle>
            <circle cx="5" cy="12" r="1"></circle>
          </svg>
        </button>
      </header>

      {/* Main content */}
      <main className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <div className="hidden sm:flex flex-col w-72 bg-white bg-opacity-70 backdrop-blur-sm border-r border-blue-100">
          <div className="p-5">
            <button className="w-full py-3 px-4 bg-gradient-to-r from-blue-600 to-blue-500 hover:from-blue-700 hover:to-blue-600 text-white rounded-xl flex items-center justify-center gap-2 transition-all shadow-md hover:shadow-lg">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="12" y1="5" x2="12" y2="19"></line>
                <line x1="5" y1="12" x2="19" y2="12"></line>
              </svg>
              New Consultation
            </button>
          </div>
          <div className="flex-1 overflow-y-auto p-3">
            <div className="mb-2">
              <h2 className="text-xs font-medium text-blue-600 px-2 py-1 uppercase tracking-wider">Recent Consultations</h2>
            </div>
            {/* Chat list items */}
            {[
              {id: 1, title: "Medication Review", preview: "About your prescription..."},
              {id: 2, title: "Symptoms Check", preview: "Headache symptoms discussed"},
              {id: 3, title: "Follow-up Consultation", preview: "Recovery progress..."}
            ].map((item) => (
              <div 
                key={item.id} 
                className="p-3 hover:bg-blue-50 rounded-xl cursor-pointer mb-2 transition-all border border-transparent hover:border-blue-100"
              >
                <h3 className="font-medium text-sm truncate">{item.title}</h3>
                <p className="text-xs text-gray-500 truncate">{item.preview}</p>
              </div>
            ))}
          </div>
          <div className="p-4 border-t border-blue-100">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center text-blue-600">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                  <circle cx="12" cy="7" r="4"></circle>
                </svg>
              </div>
              <div>
                <p className="text-sm font-medium">Patient Profile</p>
                <p className="text-xs text-gray-500">View health records</p>
              </div>
            </div>
          </div>
        </div>

        {/* Chat area */}
        <div className="flex-1 flex flex-col bg-gradient-to-br from-white to-blue-50">
          {/* Date indicator */}
          <div className="flex justify-center my-4">
            <span className="px-3 py-1 bg-blue-100 bg-opacity-50 text-blue-700 text-xs rounded-full">Today</span>
          </div>
          
          {/* Messages */}
          <div className="flex-1 overflow-y-auto px-4 md:px-6 pb-4 space-y-6">
            {/* Bot message - Doctor intro */}
            <div className="flex items-start gap-3 max-w-2xl">
              <div className="shrink-0 w-10 h-10 rounded-full bg-blue-100 border-2 border-white shadow-sm flex items-center justify-center">
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"></path>
                  <path d="M12 11h.01"></path>
                  <path d="M8 15h0"></path>
                  <path d="M16 15h0"></path>
                </svg>
              </div>
              <div className="bg-white p-4 rounded-2xl rounded-tl-none shadow-sm border border-blue-100 space-y-2">
                <p className="text-blue-700 font-medium text-sm">Dr. MediChat</p>
                <p className="text-sm text-gray-700 leading-relaxed">
                  Hello! I'm Dr. MediChat, your virtual healthcare assistant. I'm here to answer your medical questions and provide guidance. How can I help you today?
                </p>
                <p className="text-xs text-gray-400">09:30 AM</p>
              </div>
            </div>
            
            {/* User message */}
            <div className="flex items-start gap-3 max-w-2xl ml-auto">
              <div className="bg-gradient-to-r from-blue-600 to-blue-500 p-4 rounded-2xl rounded-tr-none shadow-sm space-y-2 text-white">
                <p className="text-sm leading-relaxed">
                  Hi Dr. MediChat. I've been experiencing a headache for the past two days. It's mostly on one side of my head. Should I be concerned?
                </p>
                <p className="text-xs text-blue-100">09:32 AM</p>
              </div>
              <div className="shrink-0 w-10 h-10 rounded-full bg-gray-200 border-2 border-white shadow-sm flex items-center justify-center">
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                  <circle cx="12" cy="7" r="4"></circle>
                </svg>
              </div>
            </div>

            {/* Bot message - Medical response */}
            <div className="flex items-start gap-3 max-w-2xl">
              <div className="shrink-0 w-10 h-10 rounded-full bg-blue-100 border-2 border-white shadow-sm flex items-center justify-center">
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"></path>
                  <path d="M12 11h.01"></path>
                  <path d="M8 15h0"></path>
                  <path d="M16 15h0"></path>
                </svg>
              </div>
              <div className="bg-white p-4 rounded-2xl rounded-tl-none shadow-sm border border-blue-100 space-y-2">
                <p className="text-blue-700 font-medium text-sm">Dr. MediChat</p>
                <p className="text-sm text-gray-700 leading-relaxed">
                  Thank you for sharing that. Headaches on one side can have various causes. I'd like to ask a few follow-up questions to better understand your situation:
                </p>
                <ul className="text-sm text-gray-700 list-disc pl-4 space-y-1">
                  <li>Have you experienced any nausea or sensitivity to light?</li>
                  <li>What is the pain level on a scale of 1-10?</li>
                  <li>Have you taken any medication for it?</li>
                </ul>
                <p className="text-xs text-gray-400">09:33 AM</p>
              </div>
            </div>
          </div>

          {/* Message input */}
          <div className="border-t border-blue-100 bg-white bg-opacity-70 backdrop-blur-sm p-4">
            <div className="flex items-center gap-3 max-w-4xl mx-auto">
              <button className="p-2 rounded-full hover:bg-blue-50 transition-colors text-blue-600">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"></path>
                </svg>
              </button>
              <div className="flex-1 flex items-center bg-white rounded-xl px-4 py-3 border border-blue-100 shadow-sm">
                <input 
                  type="text" 
                  placeholder="Type your health question..." 
                  className="flex-1 bg-transparent outline-none text-sm"
                />
                <div className="flex items-center gap-2">
                  <button className="text-blue-400 hover:text-blue-600 transition-colors">
                    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                      <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                      <circle cx="8.5" cy="8.5" r="1.5"></circle>
                      <polyline points="21 15 16 10 5 21"></polyline>
                    </svg>
                  </button>
                  <button className="ml-1 bg-gradient-to-r from-blue-600 to-blue-500 hover:from-blue-700 hover:to-blue-600 text-white p-2 rounded-xl transition-all shadow-sm hover:shadow-md">
                    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                      <line x1="22" y1="2" x2="11" y2="13"></line>
                      <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
                    </svg>
                  </button>
                </div>
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
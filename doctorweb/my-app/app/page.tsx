'use client';
import { Inter } from "next/font/google";
import { useRouter } from "next/navigation";
import '@fontsource-variable/playfair-display';
import { auth, provider } from "./firebase";
import { signInWithPopup, onAuthStateChanged, User } from "firebase/auth";
import { useEffect, useState } from "react";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });

export default function Home() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (firebaseUser) => {
      setUser(firebaseUser);
    });
    return () => unsubscribe();
  }, []);

  const signInWithGoogle = async () => {
    try {
      await signInWithPopup(auth, provider);
      router.push("/chat");
    } catch (err) {
      alert("Sign in failed. Please try again.");
    }
  };

  return (
    <div className={`min-h-screen flex flex-col items-center justify-center ${inter.variable} font-sans bg-gradient-to-br from-white to-blue-50`}>
      <main className="flex flex-col items-center justify-center flex-1 w-full text-center">
        <h1 className="text-5xl md:text-6xl font-bold mb-6 mt-16 text-gray-900 leading-tight">
          <span style={{ fontFamily: 'Playfair Display Variable, serif' }}>
            Leave it to MediChat
          </span>
        </h1>
        <p className="text-gray-500 text-lg max-w-2xl mb-12">
          MediChat is your AI healthcare assistant. It doesn't just answer, it delivers clarity and peace of mind. Get instant, reliable medical guidance—anytime, anywhere.
        </p>
        <button
          onClick={signInWithGoogle}
          className="rounded-full bg-blue-600 hover:bg-blue-700 text-white px-10 py-4 font-semibold text-xl shadow-lg transition mb-8"
        >
          Get Started
        </button>
      </main>
    </div>
  );
}
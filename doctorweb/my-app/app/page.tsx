'use client';
import { useRouter } from "next/navigation";
import { auth, provider } from "./firebase";
import { signInWithPopup } from "firebase/auth";
import { Inter } from "next/font/google";
import '@fontsource-variable/playfair-display';
import Image from 'next/image';
import SidebarNav from '../components/sidebarnav';
import Link from "next/link";
import { useEffect, useState } from "react";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });

export default function Home() {
  const router = useRouter();
  const [isLoaded, setIsLoaded] = useState(false);

  useEffect(() => {
    // Set isLoaded to true after component mounts
    setIsLoaded(true);
  }, []);

  const handleSignIn = async () => {
    try {
      const result = await signInWithPopup(auth, provider);
      if (result.user) {
        router.push("/chat");
      }
    } catch (err) {
      alert("Sign in failed. Please try again.");
    }
  };

  return (
    <div className={`min-h-screen flex flex-col ${inter.variable} font-sans bg-[#FFFFFF]`}>
      <div className={`stagger-container ${isLoaded ? "" : "opacity-0"}`}>
        <SidebarNav />
        {/* Navigation */}
        <header 
          className={`w-full py-4 px-6 md:px-12 flex items-center space-x-3 justify-between stagger-item ${isLoaded ? "fade-visible" : "fade-hidden"}`}
        >
          <div className="flex items-center space-x-3">
            <Link href="/">
              <Image
                src="/favicon.png"
                alt="Logo"
                width={130}
                height={130}
                className="object-contain"
                priority
              />
            </Link>
            <span className="text-xl font-semibold"></span>
          </div>
        </header>

        {/* Hero Section */}
        <main className="flex flex-col items-center justify-center flex-1 w-full px-6 md:px-12 text-center mt-50 stagger-container">
          <h1 
            className={`text-6xl md:text-6xl lg:text-7xl font-bold mb-6 mt-16 text-[#000009] leading-tight max-w-4xl stagger-item ${isLoaded ? "fade-visible" : "fade-hidden"}`}
          >
            <span style={{ fontFamily: 'Playfair Display Variable, serif' }}>
              Leave it to Bluebox
            </span>
          </h1>
          <p 
            className={`text-[#464F51] text-3xl max-w-4xl mb-12 leading-relaxed mx-auto stagger-item ${isLoaded ? "fade-visible" : "fade-hidden"}`}
          >
            Bluebox is a general AI agent that bridges minds and healthcare: it doesn't just think, it 
            delivers results. Bluebox excels at various tasks in health and life, getting everything
            done while you rest.
          </p>
          <button
            onClick={handleSignIn}
            className={`shadow-[0_0_0_3px_#000000_inset] px-6 py-2 bg-transparent border border-black dark:border-white text-black rounded-lg font-bold transform hover:-translate-y-1 transition duration-400 mb-8 btn-scale stagger-item ${isLoaded ? "fade-visible" : "fade-hidden"}`}
          >
            Get Started
          </button>
        </main>

        {/* Video Section */}
        <section 
          className={`w-full max-w-6xl mx-auto px-6 md:px-0 mb-16 mt-50 stagger-item ${isLoaded ? "fade-visible" : "fade-hidden"}`}
        >
          <div className="rounded-lg overflow-hidden relative">
            <div className="aspect-video relative">
              <iframe 
                className="absolute inset-0 w-full h-full rounded-lg shadow-lg"
                src="https://www.youtube.com/embed/u27DZMSmRew" 
                title="Nokia Future Tech Project Video!" 
                frameBorder="0" 
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" 
                referrerPolicy="strict-origin-when-cross-origin" 
                allowFullScreen
              ></iframe>
            </div>
            <div className="absolute bottom-8 left-8 z-10 pointer-events-none">
              <h2 className="text-4xl font-bold text-white drop-shadow-lg" style={{ fontFamily: 'Playfair Display Variable, serif' }}>
                Introducing<br />Bluebox
              </h2>
            </div>
          </div>
        </section>

        <section 
          className={`w-full max-w-6xl mx-auto px-6 md:px-0 mb-16 mt-50 stagger-item ${isLoaded ? "fade-visible" : "fade-hidden"}`}
          id="benchmarks" 
        >
          <div className="flex flex-col items-center justify-center">
            <div className="bg-[#F5F5F5] rounded-lg p-6">
              <h3 className="text-6xl font-bold mb-4 text-black">
                Benchmark Results
              </h3>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
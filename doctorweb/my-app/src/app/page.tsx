'use client';
import { useRouter } from "next/navigation";
import { auth, provider } from "./firebase";
import { signInWithPopup } from "firebase/auth";
import { Inter } from "next/font/google";
import '@fontsource-variable/playfair-display';
import Image from 'next/image';
import SidebarNav from '../components/sidebarnav';
import Link from "next/link";
import { useEffect, useState, useRef } from "react";
import { TypingAnimation } from "../components/typewriter";
import { motion, useAnimation, useScroll, useTransform } from "framer-motion";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });

export default function Home() {
  const router = useRouter();
  const [isLoaded, setIsLoaded] = useState(false);

  // Video section ref and scroll animation
  const videoSectionRef = useRef(null);
  const containerRef = useRef(null);
  
  // Use container as the target instead of videoSectionRef
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start start", "end start"]
  });

  // Transform scroll progress to video dimensions
  const videoWidthTransform = useTransform(
    scrollYProgress,
    [0, 0.5], 
    [510, 4000]  // Wider ratio like Charm Bears
  );
  
  const videoHeightTransform = useTransform(
    scrollYProgress,
    [0, 0.5], 
    [287, 675]  // Maintain the Charm Bears aspect ratio (16:9)
  );

  useEffect(() => {
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
    <div className={`min-h-screen flex flex-col ${inter.variable} font-sans bg-white`}>
      <div className={`stagger-container ${isLoaded ? "" : "opacity-0"}`}>
        <SidebarNav />
        {/* Navigation */}
        <header 
          className={`w-full py-4 px-6 md:px-12 flex items-center space-x-3 justify-between stagger-item ${isLoaded ? "fade-visible" : "fade-hidden"}`}
        >
          <div className="flex items-center space-x-3">
            <span className="text-xl font-semibold text-foreground"></span>
          </div>
        </header>

        {/* HERO SECTION */}
        <main className="min-h-screen flex flex-col items-center justify-center w-full px-6 md:px-12 text-center">
          <div className="max-w-2xl mx-auto flex flex-col items-center">
            <TypingAnimation
              className="text-6xl md:text-6xl lg:text-7xl font-bold mb-6 mt-16 text-black leading-tight max-w-4xl stagger-item fade-visible"
            >
              Leave it to Bluebox
            </TypingAnimation>
            <p className="text-gray-700 text-3xl max-w-4xl mb-12 leading-relaxed mx-auto fade-visible">
              Bluebox is a general AI agent that bridges minds and healthcare: it doesn't just think, it 
              delivers results. Bluebox excels at various tasks in health and life, getting everything
              done while you rest.
            </p>
            <button
              onClick={handleSignIn}
              className="px-6 py-2 border border-gray-300 rounded-lg font-bold bg-white text-black hover:bg-gray-100 transition mb-8 fade-visible"
            >
              Get Started
            </button>
          </div>
        </main>

        {/* Video container that will hold the sticky section */}
        <div ref={containerRef} className="relative w-full h-[250vh]">
          {/* Sticky video section */}
          <section 
            ref={videoSectionRef}
            className="w-screen pt-10 text-center fade-visible flex flex-col items-center justify-start sticky top-0 h-screen z-10 bg-white"
          >
            <h1 className="text-7xl font-bold mb-2 text-[#3b2314] font-serif">Bluebox</h1>
            <p className="text-2xl text-gray-700 mb-8">Your AI companion for health and wellness</p>
            
            <div className="flex w-full items-start justify-center px-4">
              <div className="relative flex items-center justify-center w-full max-w-6xl">
                {/* Left decorative panel */}
                <div className="hidden md:block w-1/6 h-full bg-gradient-to-r from-blue-50 to-blue-100 rounded-l-2xl overflow-hidden">
                  <div className="pattern-dots-lg text-blue-200 h-full opacity-70"></div>
                </div>
                
                {/* Video container */}
                <motion.div
                  className="rounded-lg overflow-hidden shadow-2xl relative z-10 mx-2"
                  style={{ 
                    width: videoWidthTransform,
                    height: videoHeightTransform,
                    maxWidth: "70vw",
                  }}
                >
                  <iframe
                    className="absolute inset-0 w-full h-full rounded-lg"
                    src="https://www.youtube.com/embed/u27DZMSmRew"
                    title="Nokia Future Tech Project Video!"
                    frameBorder="0"
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
                    referrerPolicy="strict-origin-when-cross-origin"
                    allowFullScreen
                  ></iframe>
                </motion.div>
                
                {/* Right decorative panel */}
                <div className="hidden md:block w-1/6 h-full bg-gradient-to-l from-blue-50 to-blue-100 rounded-r-2xl overflow-hidden">
                  <div className="pattern-dots-lg text-blue-200 h-full opacity-70"></div>
                </div>
              </div>
            </div>
            
            <div className="mt-10 flex space-x-4">
              <button className="px-8 py-3 bg-[#3b2314] text-white rounded-full font-bold hover:bg-[#5c3920] transition shadow-lg">
                Get Started Now
              </button>
              <button className="px-8 py-3 border-2 border-[#3b2314] text-[#3b2314] rounded-full font-bold hover:bg-[#f5f0ea] transition">
                Learn More
              </button>
            </div>
          </section>
        </div>

        {/* About Section - Modernized */}
        <section id="about" className="relative w-full px-6 py-24 text-center fade-visible z-20 bg-gradient-to-b from-white to-blue-50">
          <div className="max-w-4xl mx-auto">
            <motion.h2 
              className="text-5xl font-bold mb-6 text-[#3b2314]" 
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
              viewport={{ once: true }}
            >
              About Bluebox.ai
            </motion.h2>
            <motion.p 
              className="text-xl text-gray-700 mb-8 leading-relaxed"
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.2 }}
              viewport={{ once: true }}
            >
              Bluebox.ai is your trusted AI companion for health, productivity, and life. Our mission is to bridge minds and healthcare, making advanced AI accessible and helpful for everyone.
            </motion.p>
            <motion.div
              className="w-20 h-1 bg-blue-500 mx-auto"
              initial={{ width: 0 }}
              whileInView={{ width: 80 }}
              transition={{ duration: 0.8 }}
              viewport={{ once: true }}
            />
          </div>
        </section>

        {/* Use Cases Section - Modernized with animations */}
        <section id="use-cases" className="w-full px-6 py-24 bg-white">
          <div className="max-w-6xl mx-auto">
            <motion.h2 
              className="text-5xl font-bold mb-16 text-[#3b2314] text-center"
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
              viewport={{ once: true }}
            >
              Use Cases
            </motion.h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-12">
              <motion.div 
                className="bg-white rounded-xl p-8 shadow-xl hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-2 border border-gray-100"
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.1 }}
                viewport={{ once: true }}
              >
                <div className="w-16 h-16 rounded-full bg-blue-100 flex items-center justify-center mb-6 mx-auto">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <h3 className="text-2xl font-bold mb-4 text-[#3b2314] text-center">Health Q&A</h3>
                <p className="text-gray-700 text-center">Get instant answers to your health questions, 24/7, powered by advanced AI models.</p>
              </motion.div>
              
              <motion.div 
                className="bg-white rounded-xl p-8 shadow-xl hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-2 border border-gray-100"
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.3 }}
                viewport={{ once: true }}
              >
                <div className="w-16 h-16 rounded-full bg-green-100 flex items-center justify-center mb-6 mx-auto">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                  </svg>
                </div>
                <h3 className="text-2xl font-bold mb-4 text-[#3b2314] text-center">Productivity</h3>
                <p className="text-gray-700 text-center">Organize your tasks, set reminders, and boost your productivity with smart suggestions.</p>
              </motion.div>
              
              <motion.div 
                className="bg-white rounded-xl p-8 shadow-xl hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-2 border border-gray-100"
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.5 }}
                viewport={{ once: true }}
              >
                <div className="w-16 h-16 rounded-full bg-purple-100 flex items-center justify-center mb-6 mx-auto">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 text-purple-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
                  </svg>
                </div>
                <h3 className="text-2xl font-bold mb-4 text-[#3b2314] text-center">Lifestyle Guidance</h3>
                <p className="text-gray-700 text-center">Receive personalized tips for wellness, nutrition, and daily routines tailored to you.</p>
              </motion.div>
            </div>
          </div>
        </section>

        {/* Community Section */}
        <section id="community" className="w-full max-w-4xl mx-auto px-6 py-20 text-center fade-visible">
          <h2 className="text-4xl font-bold mb-4 text-black">Community</h2>
          <p className="text-lg text-gray-700 mb-2">
            Join our growing community to share experiences, ask questions, and help shape the future of Bluebox.ai.
          </p>
          <a href="#" className="inline-block mt-4 px-6 py-2 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition">Join the Community</a>
        </section>

        {/* Benchmarks Section */}
        <section id="benchmarks" className="w-full max-w-6xl mx-auto px-6 py-20 fade-visible">
          <h2 className="text-4xl font-bold mb-8 text-black text-center">Benchmark Results</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="bg-gray-50 rounded-xl p-6 shadow-md fade-visible">
              <h3 className="text-2xl font-semibold mb-2 text-black">Speed</h3>
              <p className="text-gray-700">Bluebox.ai responds in under 2 seconds for most queries, ensuring a seamless experience.</p>
            </div>
            <div className="bg-gray-50 rounded-xl p-6 shadow-md fade-visible">
              <h3 className="text-2xl font-semibold mb-2 text-black">Accuracy</h3>
              <p className="text-gray-700">Our AI achieves over 95% accuracy on standard health and productivity benchmarks.</p>
            </div>
            <div className="bg-gray-50 rounded-xl p-6 shadow-md fade-visible">
              <h3 className="text-2xl font-semibold mb-2 text-black">User Satisfaction</h3>
              <p className="text-gray-700">Rated 4.9/5 by thousands of users for helpfulness, clarity, and ease of use.</p>
            </div>
          </div>
        </section>

        {/* Pricing Section */}
        <section id="pricing" className="w-full max-w-4xl mx-auto px-6 py-20 text-center fade-visible">
          <h2 className="text-4xl font-bold mb-4 text-black">Pricing</h2>
          <div className="flex flex-col md:flex-row justify-center gap-8 mt-8">
            <div className="bg-gray-50 rounded-xl p-8 shadow-md flex-1 fade-visible">
              <h3 className="text-2xl font-semibold mb-2 text-black">Free</h3>
              <p className="text-gray-700 mb-4">Basic access to Bluebox.ai features</p>
              <p className="text-3xl font-bold text-black mb-4">$0</p>
              <button className="px-6 py-2 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition">Get Started</button>
            </div>
            <div className="bg-gray-50 rounded-xl p-8 shadow-md flex-1 fade-visible">
              <h3 className="text-2xl font-semibold mb-2 text-black">Pro</h3>
              <p className="text-gray-700 mb-4">Advanced features and priority support</p>
              <p className="text-3xl font-bold text-black mb-4">$9/mo</p>
              <button className="px-6 py-2 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition">Upgrade</button>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
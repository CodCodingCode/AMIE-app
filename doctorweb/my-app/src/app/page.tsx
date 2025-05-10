'use client';
import { useRouter } from "next/navigation";
import { auth, provider } from "./firebase";
import { signInWithPopup } from "firebase/auth";
import { useEffect, useState } from "react";
import { TypingAnimation } from "../components/type";
import { motion } from "framer-motion";
import NavBar from "../components/navigation";
import { fadeInUp } from "../animations/fades";
import { Button } from "../components/buttons";

export default function Home() {
  const router = useRouter();
  const [isLoaded, setIsLoaded] = useState(false);

  useEffect(() => {
    setIsLoaded(true);
  }, []);

  const handleSignIn = async () => {
    await signInWithPopup(auth, provider);
    router.push("/chat");
  };

  return (
    <div className="min-h-screen flex flex-col bg-[var(--white)]">
      <div className={`stagger-container ${isLoaded ? "" : "opacity-0"}`}>
        <NavBar />
        
        {/* HERO SECTION */}
        <main className="min-h-screen flex flex-col items-center justify-center w-full px-6 md:px-12 text-center pt-24 font-[Inter]">
          <div className="max-w-5xl mx-auto flex flex-col items-center">
            <div>
              <TypingAnimation
                className="text-6xl font-bold mb-8 text-[var(--outer-space)] font-serif"
              >
                Enter the Bluebox
              </TypingAnimation>
              <p className="text-xl text-[var(--outer-space)] mb-8 max-w-2xl mx-auto">
                Bluebox is a general AI agent that bridges minds and actions: it doesn't just think, it delivers results. Bluebox excels at various tasks in work and life, getting everything done while you rest.
              </p>
                <Button
                  onClick={handleSignIn}
                >
                Get Started
              </Button>
            </div>
          </div>
        </main>

        {/* YOUTUBE VIDEO SECTION */}
        <section className="w-full flex flex-col items-center justify-center bg-[var(--white)] font-[Inter]">
          <motion.div 
            className="w-[1600px] h-[900px] w-full max-w-4xl aspect-video rounded-xl overflow-hidden shadow-lg mt-8"
            {...fadeInUp}
          >
            <iframe
              src="https://www.youtube.com/embed/TJcHyfzkXf4"
              title="Demo Video"
              frameBorder="0"
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
              referrerPolicy="strict-origin-when-cross-origin"
              allowFullScreen
              className="w-full h-full"
            ></iframe>
          </motion.div>


          {/* BUTTONS SECTION */}
          <motion.div 
            className="flex flex-col md:flex-row gap-4 justify-center mt-8"
            {...fadeInUp}
          >
            <button
              className="btn-primary px-8 py-3 rounded-full text-lg font-semibold shadow-md transition"
            >
              Try Bluebox
            </button>
            <button
              className="btn-secondary px-8 py-3 rounded-full text-lg font-semibold shadow-md transition"
            >
              Download the App
            </button>
          </motion.div>
        </section>

        <section className="w-full flex flex-col items-center justify-center py-16 font-[Inter] py-60">
        <motion.h2 
          className="text-5xl font-bold mb-16 text-[var(--outer-space)] text-center font-serif"
          {...fadeInUp}
        >
          Bluebox's capabilities
        </motion.h2>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 w-full max-w-7xl px-4">
          {[
            {
              title: "Advanced reasoning",
              text: "Bluebox can perform complex cognitive tasks that go beyond simple pattern recognition or text generation.",
              icon: (
                <svg width="72" height="72" viewBox="0 0 72 72" fill="none">
                  <circle cx="36" cy="36" r="32" fill="#e5e3db" />
                  <path d="M36 16L36 56M16 36L56 36M24 24L48 48M48 24L24 48" stroke="#222" strokeWidth="3" strokeLinecap="round"/>
                </svg>
              )
            },
            {
              title: "Vision analysis",
              text: "Transcribe and analyze almost any static image, from handwritten notes and graphs, to photographs.",
              icon: (
                <svg width="72" height="72" viewBox="0 0 72 72" fill="none">
                  <rect x="12" y="12" width="48" height="48" rx="12" fill="#e5e3db" />
                  <circle cx="36" cy="36" r="12" stroke="#222" strokeWidth="3" fill="none"/>
                  <path d="M24 24L48 48M48 24L24 48" stroke="#222" strokeWidth="3" strokeLinecap="round"/>
                </svg>
              )
            },
            {
              title: "Code generation",
              text: "Start creating websites in HTML and CSS, turning images into structured data, or debugging complex code bases.",
              icon: (
                <svg width="72" height="72" viewBox="0 0 72 72" fill="none">
                  <rect x="12" y="20" width="48" height="32" rx="6" fill="#e5e3db" />
                  <rect x="20" y="32" width="32" height="8" rx="2" fill="#fff" />
                  <path d="M28 36H44" stroke="#222" strokeWidth="3" strokeLinecap="round"/>
                </svg>
              )
            },
            {
              title: "Multilingual processing",
              text: "Translate between various languages in real-time, practice grammar, or create multilingual content.",
              icon: (
                <svg width="72" height="72" viewBox="0 0 72 72" fill="none">
                  <ellipse cx="24" cy="36" rx="16" ry="14" fill="#e5e3db" />
                  <ellipse cx="48" cy="36" rx="16" ry="14" fill="#e5e3db" />
                  <ellipse cx="24" cy="36" rx="14" ry="12" stroke="#222" strokeWidth="3" fill="none"/>
                  <ellipse cx="48" cy="36" rx="14" ry="12" stroke="#222" strokeWidth="3" fill="none"/>
                </svg>
              )
            }
          ].map((feature, i) => (
            <motion.div 
              key={i}
              className="flex flex-col items-center text-center"
              {...fadeInUp}
              transition={{ ...fadeInUp.transition, delay: 0.1 * i }}
            >
              <span className="mb-6">{feature.icon}</span>
              <h3 className="text-2xl font-bold mb-4 text-[var(--outer-space)]">{feature.title}</h3>
              <p className="text-lg text-[var(--outer-space)]">{feature.text}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* About Section */}
      <section id="about" className="relative w-full px-6 py-24 font-[Inter]">
        <div className="max-w-4xl mx-auto flex flex-col md:flex-row items-start gap-12">
          {/* Left: Heading and Paragraph */}
          <div className="flex-1">
            <motion.h2 
              className="text-5xl font-bold mb-6 text-[var(--outer-space)] font-serif"
              {...fadeInUp}
            >
              About Bluebox.ai
            </motion.h2>
            <motion.p 
              className="text-xl text-[var(--outer-space)] leading-relaxed"
              {...fadeInUp}
            >
              Bluebox.ai is your trusted AI companion for health, productivity, and life. Our mission is to bridge minds and healthcare, making advanced AI accessible and helpful for everyone.
            </motion.p>
          </div>
          {/* Right: Empty space for image */}
          <div className="flex-1 flex items-center justify-center">
            {/* Placeholder for future image */}
            <div className="w-full h-64 bg-[var(--beige)] rounded-xl border-2 border-dashed border-[var(--ash-gray)] flex items-center justify-center text-[var(--ash-gray)]">
              {/* You can put an <img> or illustration here later */}
              Image coming soon
            </div>
          </div>
        </div>
      </section>

      {/* Community Section */}
      <section id="community" className="w-full max-w-4xl mx-auto px-6 py-20 text-center font-[Inter]">
        <motion.h2 
          className="text-4xl font-bold mb-4 text-[var(--black)] font-serif"
          {...fadeInUp}
        >
          Community
        </motion.h2> 
        <motion.p 
          className="text-lg text-[var(--outer-space)] mb-2"
          {...fadeInUp}
        >
          Join our growing community to share experiences, ask questions, and help shape the future of Bluebox.ai.
        </motion.p>
        <motion.button
          onClick={() => window.location.href = '#'}
          className="mt-4 px-6 py-2 border border-[var(--ash-gray)] rounded-lg font-bold bg-[var(--white)] text-[var(--black)] hover:bg-[var(--light-cyan)] transition-colors"
          {...fadeInUp}
        >
          Join the Community
        </motion.button>
      </section>

      {/* BENCHMARKS SECTION */}
      <section id="benchmarks" className="w-full max-w-6xl mx-auto px-6 py-20 font-[Inter]">
        <motion.h2 
          className="text-4xl font-bold mb-8 text-[var(--black)] text-center font-serif"
          {...fadeInUp}
        >
          Benchmark Results
        </motion.h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {[
            {
              title: "Speed",
              description: "Bluebox.ai responds in under 2 seconds for most queries, ensuring a seamless experience."
            },
            {
              title: "Accuracy",
              description: "Our AI achieves over 95% accuracy on standard health and productivity benchmarks."
            },
            {
              title: "User Satisfaction",
              description: "Rated 4.9/5 by thousands of users for helpfulness, clarity, and ease of use."
            }
          ].map((item, index) => (
            <motion.div
              key={index}
              className="bg-[var(--snow-drift)] rounded-xl p-6 shadow-md"
              {...fadeInUp}
              transition={{ ...fadeInUp.transition, delay: 0.1 * index }}
            >
              <motion.h3 
                className="text-2xl font-semibold mb-2 text-[var(--black)] font-serif"
                {...fadeInUp}
              >
                {item.title}
              </motion.h3>
              <motion.p 
                className="text-[var(--outer-space)]"
                {...fadeInUp}
              >
                {item.description}
              </motion.p>
            </motion.div>
          ))}
        </div>
      </section>
      </div>
    </div>
  );
}
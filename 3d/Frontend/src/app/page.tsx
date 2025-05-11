'use client'

import React, { useEffect, useState } from 'react'
import dynamic from 'next/dynamic'
import { motion } from 'framer-motion'
import Navigation from './components/navigation'
import Footer from './components/footer'
import Image from 'next/image'
import { fadeInUp } from './animations/fades'

// Import portal scene dynamically
const PortalScene = dynamic(
  () => import('./components/portalcomplete'),
  { 
    ssr: false,
    loading: () => <div className="h-screen w-full bg-black" />
  }
)


export default function Home() {
  const [isLoaded, setIsLoaded] = useState(false);

  useEffect(() => {
    setIsLoaded(true);
  }, []);

  return (
    <div className="min-h-screen flex flex-col">
      <div className={`stagger-container ${isLoaded ? "" : "opacity-0"}`}>
        <Navigation />
        <section className="h-screen">
          <PortalScene />
        </section>
        
        {/* About Section */}
        <section className="py-16">
        <div className="max-w-4xl mx-auto flex flex-col md:flex-row items-start gap-12 px-4">
          {/* Left: Heading and Paragraph */}
          <div className="flex-1">
            <motion.h2 
              className="text-5xl font-bold mb-6 text-[var(--outer-space)] font-serif"
              {...fadeInUp}
            >
              About<br/>Bluebox.ai
            </motion.h2>
            <motion.p 
              className="text-xl text-[var(--outer-space)] leading-relaxed"
              {...fadeInUp}
            >
              Bluebox.ai is your trusted AI companion for health, productivity, and life. Our mission is to bridge minds and healthcare, making advanced AI accessible and helpful for everyone.
            </motion.p>
          </div>
          {/* Right: Image placeholder */}
          <div className="flex-1 flex items-center justify-center">
            <div className="w-full aspect-square rounded-xl border border-dashed border-[var(--ash-gray)] flex items-center justify-center text-[var(--ash-gray)] bg-[var(--beige)]">
              <span className="text-lg">Image coming soon</span>
            </div>
          </div>
        </div>
      </section>
      
      {/* BENCHMARKS SECTION */}
      <section className="py-16 px-4">
        <motion.h2 
          className="text-4xl font-bold mb-12 text-[var(--outer-space)] text-center font-serif"
          {...fadeInUp}
        >
          Benchmark Results
        </motion.h2>
        <motion.div 
          className="flex justify-center mx-auto w-full max-w-4xl aspect-video rounded-xl overflow-hidden shadow-lg"
          {...fadeInUp}
        >
          <Image 
            src="/benchmarks.png" 
            alt="Benchmark Results" 
            width={1200} 
            height={675} 
            priority
            quality={90}
            className="rounded-lg shadow-md"
          />
        </motion.div>
      </section>
        
        {/* Footer */}
        <Footer />
      </div>
    </div>
  )
}

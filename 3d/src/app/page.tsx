'use client'

import React, { useEffect, useState } from 'react'
import dynamic from 'next/dynamic'
import { motion } from 'framer-motion'

// Import PortalScene component with no SSR to avoid hydration issues
// This is necessary because Three.js needs the browser environment
const PortalScene = dynamic(
  () => import('./components/portalcomplete'),
  { ssr: false }
)

// Animation variants
const fadeInUp = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.6 }
}

export default function Home() {
  const [isLoaded, setIsLoaded] = useState(false);

  useEffect(() => {
    setIsLoaded(true);
  }, []);

  return (
    <div className="min-h-screen flex flex-col">
      <div className={`stagger-container ${isLoaded ? "" : "opacity-0"}`}>
        <section className="h-screen">
          <PortalScene />
        </section>
        
        {/* About Section */}
        <section id="about" className="relative w-full py-24 px-6 font-[Inter]">
          <div className="max-w-4xl mx-auto flex flex-col md:flex-row items-start gap-12">
            {/* Left: Heading and Paragraph */}
            <div className="flex-1">
              <motion.h2 
                className="text-5xl font-bold mb-6 text-[var(--outer-space)] font-serif"
                initial="initial"
                animate="animate"
                variants={fadeInUp}
              >
                About<br/>Bluebox.ai
              </motion.h2>
              <motion.p 
                className="text-xl text-[var(--outer-space)] leading-relaxed"
                initial="initial"
                animate="animate"
                variants={fadeInUp}
                transition={{ delay: 0.2 }}
              >
                Bluebox.ai is your trusted AI companion for health, productivity, and life. Our mission is to bridge minds and healthcare, making advanced AI accessible and helpful for everyone.
              </motion.p>
            </div>
            {/* Right: Image placeholder */}
            <div className="flex-1 flex items-center justify-center">
              <div className="w-full aspect-square rounded-xl border border-dashed border-[var(--ash-gray)] flex items-center justify-center text-[var(--ash-gray)] bg-[var(--beige)]">
                <span className="text-lg">Image coming soon yes</span>
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>
  )
}

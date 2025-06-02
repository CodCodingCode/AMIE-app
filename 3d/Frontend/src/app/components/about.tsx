'use client';

import { motion } from "framer-motion";
import Image from "next/image";
import { fadeInUp, defaultTransition } from "@/app/lib/utils";

export default function About() {
    return (
        <section id = "about" className="bg-neutral-900 pt-24 pb-16">
        <div className="max-w-4xl mx-auto flex flex-col md:flex-row items-start gap-12 px-4">
        {/* Left: Heading and Paragraph */}
        <div className="flex-1">
            <motion.h2 
            variants={fadeInUp}
            initial="initial"
            whileInView="animate"
            viewport={{ once: true }}
            transition={defaultTransition}
            className="text-5xl font-bold mb-6 text-white font-serif"
            >
            About<br/>Bluebox.ai
            </motion.h2>
            <motion.p 
            variants={fadeInUp}
            initial="initial"
            whileInView="animate"
            viewport={{ once: true }}
            transition={{ ...defaultTransition, delay: 0.2 }}
            className="text-xl text-white leading-relaxed"
            >
            Bluebox.ai is your trusted AI companion for health, productivity, and life. Our mission is to bridge minds and healthcare, making advanced AI accessible and helpful for everyone.
            </motion.p>
        </div>
        {/* Right: Image container */}
        <motion.div 
        variants={fadeInUp}
        initial="initial"
        whileInView="animate"
        viewport={{ once: true }}
        transition={{ ...defaultTransition, delay: 0.4 }}
        className="flex-1 flex items-center justify-center"
        >
            <div className="w-full h-full max-w-[800px] rounded-xl overflow-hidden">
            <Image 
                src="/about.jpg" 
                alt="Doctor Image" 
                width={1200} 
                height={800}
                className="w-full h-full object-cover object-center"
                priority
            />
            </div>
        </motion.div>
        </div>
        </section>
    )
}
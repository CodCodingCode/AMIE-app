'use client';

import { motion } from "framer-motion";
import Image from "next/image";
import { fadeInUp, defaultTransition } from "@/app/lib/utils";

export default function Benchmarks() {
    return (
    <section id = "benchmarks" className="bg-neutral-900 py-16 pb-48 px-4">
        <motion.h2 
            variants={fadeInUp}
            initial="initial"
            whileInView="animate"
            viewport={{ once: true }}
            transition={defaultTransition}
            className="text-4xl font-bold mb-12 text-white text-center font-serif"
            >
        Benchmark Results
        </motion.h2>
        <motion.div 
        variants={fadeInUp}
        initial="initial"
        whileInView="animate"
        viewport={{ once: true }}
        transition={{ ...defaultTransition, delay: 0.2 }}
        className="flex justify-center mx-auto w-full max-w-4xl aspect-video rounded-xl overflow-hidden shadow-lg"
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
    )
}
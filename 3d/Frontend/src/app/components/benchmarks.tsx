import { motion } from "framer-motion";
import Image from "next/image";
import { fadeInUp } from "../animations/fades"

export default function Benchmarks() {
    return (
    <section id = "benchmarks" className="py-16 pb-48 px-4">
        <motion.h2 
            className="text-4xl font-bold mb-12 text-outerSpace text-center font-serif"
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
    )
}
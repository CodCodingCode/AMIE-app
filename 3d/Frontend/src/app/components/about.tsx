import { motion } from "framer-motion";
import Image from "next/image";
import { fadeInUp } from "../animations/fades"

export default function About() {
    return (
        <section id = "about" className="py-16 pt-64">
        <div className="max-w-4xl mx-auto flex flex-col md:flex-row items-start gap-12 px-4">
        {/* Left: Heading and Paragraph */}
        <div className="flex-1">
            <motion.h2 
            className="text-5xl font-bold mb-6 text-outerSpace font-serif"
            {...fadeInUp}
            >
            About<br/>Bluebox.ai
            </motion.h2>
            <motion.p 
            className="text-xl text-outerSpace leading-relaxed"
            {...fadeInUp}
            >
            Bluebox.ai is your trusted AI companion for health, productivity, and life. Our mission is to bridge minds and healthcare, making advanced AI accessible and helpful for everyone.
            </motion.p>
        </div>
        {/* Right: Image container */}
        <div className="flex-1 flex items-center justify-center">
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
        </div>
        </div>
        </section>
    )
}
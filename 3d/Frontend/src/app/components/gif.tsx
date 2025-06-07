import { motion } from 'framer-motion';
import { cn, fadeInUp, staggerContainer, defaultTransition, fadeInLeft } from '../lib/utils';

export default function Gif() {
    return (
        <motion.div 
            className={cn("flex items-center justify-center px-10 py-10 bg-neutral-900")}
            variants={staggerContainer}
            initial="initial"
            whileInView="animate"
            viewport={{ once: true, amount: 0.3 }}
        >
            {/* Main Container with Outline */}
            <motion.div 
                className={cn(
                    "flex items-center border border-gray-600/50 rounded-3xl",
                    "bg-gray-800/20 backdrop-blur-sm overflow-hidden max-w-7xl w-full"
                )}
                variants={fadeInUp}
                transition={defaultTransition}
            >
                {/* Text Section */}
                <motion.div 
                    className="flex-1 text-white px-12 py-16"
                    variants={fadeInLeft}
                    transition={defaultTransition}
                >
                    <h1 className={cn("text-5xl font-bold mb-6")}>
                        Perfect search over humans
                    </h1>
                    <p className={cn("text-gray-300 mb-6 text-lg leading-relaxed")}>
                        Clado filters through millions of profiles to surface genuinely relevant people — not random matches. The results feel like magic, but it's pure AI precision.
                    </p>
                </motion.div>

                {/* Vertical Divider Line */}
                <div className={cn("w-px h-96 bg-gray-600/50")}></div>

                {/* GIF Section */}
                <motion.div 
                    className="flex-1 px-12 py-16"
                    variants={fadeInUp}
                    transition={defaultTransition}
                >
                    <img 
                        src="/consultations.gif" 
                        alt="demo"
                        className={cn("rounded-2xl w-full h-auto")}
                    />
                </motion.div>
            </motion.div>
        </motion.div>
    );
}
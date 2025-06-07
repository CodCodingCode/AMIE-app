import { motion } from 'framer-motion';
import { cn, fadeInUp, staggerContainer, defaultTransition, fadeInLeft } from '../lib/utils';

export default function Main() {
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
                {/* GIF Section (Now on the Left) */}
                <motion.div 
                    className="flex-1 px-12 py-16"
                    variants={fadeInUp}
                    transition={defaultTransition}
                >
                    <img 
                        src="/main.gif" 
                        alt="demo"
                        className={cn("rounded-2xl w-full h-auto")}
                    />
                </motion.div>

                {/* Vertical Divider Line */}
                <div className={cn("w-px h-96 bg-gray-600/50")}></div>

                {/* Text Section (Now on the Right) */}
                <motion.div 
                    className="flex-1 text-white px-12 py-16"
                    variants={fadeInLeft}
                    transition={defaultTransition}
                >
                    <h1 className={cn("text-5xl font-bold mb-6")}>
                        Discover talent with laser focus
                    </h1>
                    <p className={cn("text-gray-300 mb-6 text-lg leading-relaxed")}>
                        Clado doesn't just match keywords — it understands context, experience, and fit. Uncover the exact people you're looking for, faster than ever before.
                    </p>
                </motion.div>
            </motion.div>
        </motion.div>
    );
}
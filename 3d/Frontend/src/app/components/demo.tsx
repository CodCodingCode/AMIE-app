import { cn, fadeInUp, staggerContainer, defaultTransition } from '../lib/utils';
import { motion } from 'framer-motion';
import { useBlueboxAnimation } from '@/app/lib/hooks';

export default function Demo() {
  const { handleGetStartedClick } = useBlueboxAnimation();

  return (
    <motion.section 
      className={cn("min-h-screen bg-neutral-900 flex flex-col items-center justify-center px-4")}
      variants={staggerContainer}
      initial="initial"
      animate="animate"
    >
      {/* Logo */}
      <motion.div 
        className="mb-16"
        variants={fadeInUp}
        transition={defaultTransition}
      >
        <img 
          src="/reallogo.png" 
          alt="AI Doctor Logo" 
          className={cn("w-40 h-40 rounded-2xl shadow-lg")}
        />
      </motion.div>

      {/* Main Heading */}
      <motion.div 
        className="text-center max-w-4xl mb-12"
        variants={fadeInUp}
        transition={defaultTransition}
      >
        <h1 className={cn("text-5xl md:text-6xl font-bold text-white leading-tight")}>
          We diagnose the complex cases
          <br />
          <span className="block mt-2">
            so you can focus on healing.
          </span>
        </h1>
      </motion.div>

      {/* CTA Button */}
      <motion.button 
        className={cn(
          "bg-dukeBlue hover:bg-dukeBlue text-white font-semibold py-4 px-8",
          "rounded-full text-lg transition-colors duration-200 shadow-lg",
          "hover:shadow-xl transform hover:scale-105"
        )}
        variants={fadeInUp}
        transition={defaultTransition}
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        onClick={handleGetStartedClick}
      >
        Get a consultation
      </motion.button>
    </motion.section>
  );
}
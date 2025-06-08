import Image from "next/image";
import { motion } from "framer-motion";
import { fadeInUp, fadeInLeft, staggerContainer, defaultTransition, fadeinRight } from "../lib/utils";

export default function People() {
  return (
    <motion.section
      className="bg-neutral-900 text-white px-10 py-24"
      variants={staggerContainer}
      initial="initial"
      whileInView="animate"
      viewport={{ once: true, amount: 0.3 }}
    >
      {/* Heading */}
      <motion.h2
        className="text-5xl font-bold text-center mb-16"
        variants={fadeInUp}
        transition={defaultTransition}
      >
        Who we are
      </motion.h2>

      {/* Content Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-12 max-w-6xl mx-auto items-center">
        {/* Text */}
        <motion.div
          className="space-y-6 text-lg leading-relaxed text-gray-300"
          variants={fadeinRight}
          transition={defaultTransition}
        >
          <p>
            We're a collective of passionate developers, designers, and builders who craft elegant, scalable digital experiences.
          </p>
          <p>
            Whether it's designing seamless user interfaces or solving complex engineering challenges, our mission is to deliver thoughtful, innovative solutions that drive impact.
          </p>
        </motion.div>

        {/* Image */}
        <motion.div
          className="w-full h-64 md:h-80 rounded-2xl overflow-hidden bg-gray-800 flex items-center justify-center"
          variants={fadeInUp}
          transition={defaultTransition}
        >
          <Image
            src="/team-placeholder.png" // Replace with your image
            alt="Our team"
            width={500}
            height={500}
            className="object-cover w-full h-full"
          />
        </motion.div>
      </div>
    </motion.section>
  );
}

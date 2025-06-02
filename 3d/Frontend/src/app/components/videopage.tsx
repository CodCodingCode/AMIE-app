'use client';

import { motion } from "framer-motion";
import { fadeInUp, defaultTransition } from "@/app/lib/utils";

export default function Videopage() {
  return (
    <section className="bg-neutral-900 pb-24">
            <div className="container mx-auto px-4 pt-24">
            <motion.h2 
          variants={fadeInUp}
          initial="initial"
          whileInView="animate"
          viewport={{ once: true }}
          transition={defaultTransition}
                className="text-6xl font-bold mb-12 text-white text-center font-serif"
                >
            Welcome to the Bluebox
            </motion.h2>
            <motion.div
          variants={fadeInUp}
          initial="initial"
          whileInView="animate"
          viewport={{ once: true }}
          transition={{ ...defaultTransition, delay: 0.2 }}
                className="mx-auto"
            >
                <video
                className="rounded-xl shadow-lg w-full max-w-[1600px] aspect-video overflow-hidden"
                controls
                src="/videoplayback.mp4"
              >
                Your browser does not support the video tag.
              </video>
            </motion.div>
        </div>
    </section>
  );
}
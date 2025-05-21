import { motion } from "framer-motion";
import { fadeInUp } from "../animations/fades";

export default function Videopage() {
  return (
    <section className="bg-white pb-24">
            <div className="container mx-auto px-4 bg-white">
            <motion.h2 
                className="text-6xl font-bold mb-12 text-black text-center font-serif"
                {...fadeInUp}
                >
            Welcome to the Bluebox
            </motion.h2>
            <motion.div
                className="mx-auto"
                variants={fadeInUp}
                initial="hidden"
                animate="visible"
            >
                <video
                className="w-full rounded-xl shadow-lg w-[1600px] h-[900px]"
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
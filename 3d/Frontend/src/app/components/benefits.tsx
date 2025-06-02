'use client';

import { motion } from 'framer-motion';
import Image from 'next/image';
import { fadeInLeft, fadeInUp, defaultTransition } from '@/app/lib/utils';

const benefits = [
  {
    number: 1,
    title: "Quick Consultation",
    description: "Get instant medical guidance without the wait times of traditional healthcare"
  },
  {
    number: 2,
    title: "Smart Analysis",
    description: "Our AI analyzes your symptoms and medical history for personalized care"
  },
  {
    number: 3,
    title: "Follow-up Care",
    description: "Receive ongoing support and monitoring for your health journey"
  }
];

export default function Benefits() {
  return (
    <section className="py-24 px-4 bg-neutral-950">
      <div className="max-w-7xl mx-auto">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
          <motion.div
            variants={fadeInLeft}
            initial="initial"
            whileInView="animate"
            viewport={{ once: true }}
            transition={defaultTransition}
          >
            <h2 className="text-4xl font-bold text-white mb-6 font-serif">
              Healthcare Made Simple
            </h2>
            <div className="space-y-6">
              {benefits.map((benefit) => (
                <motion.div
                  key={benefit.number}
                  variants={fadeInUp}
                  transition={{ ...defaultTransition, delay: benefit.number * 0.1 }}
                  className="flex items-start"
                >
                <div className="flex-shrink-0 w-12 h-12 bg-blue-500/10 rounded-full flex items-center justify-center">
                    <span className="text-blue-500 text-2xl">{benefit.number}</span>
                </div>
                <div className="ml-4">
                    <h3 className="text-xl font-semibold text-white mb-2">{benefit.title}</h3>
                    <p className="text-gray-400">{benefit.description}</p>
                </div>
                </motion.div>
              ))}
            </div>
          </motion.div>
          
          <motion.div
            variants={fadeInUp}
            initial="initial"
            whileInView="animate"
            viewport={{ once: true }}
            transition={defaultTransition}
            className="relative h-[600px] rounded-2xl overflow-hidden"
          >
            <Image
              src="https://images.pexels.com/photos/7579831/pexels-photo-7579831.jpeg"
              alt="Healthcare Technology"
              fill
              className="object-cover"
            />
          </motion.div>
        </div>
      </div>
    </section>
  );
}
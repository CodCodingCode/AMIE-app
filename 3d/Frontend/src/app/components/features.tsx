'use client';

import { motion } from 'framer-motion';
import { IconBrain, IconHeartRateMonitor, IconShieldLock, IconClock } from '@tabler/icons-react';

const features = [
  {
    icon: IconBrain,
    title: "Advanced AI Technology",
    description: "Powered by state-of-the-art machine learning models for accurate medical guidance"
  },
  {
    icon: IconHeartRateMonitor,
    title: "Symptom Analysis",
    description: "Comprehensive analysis of symptoms with detailed health insights"
  },
  {
    icon: IconShieldLock,
    title: "Secure & Private",
    description: "Your health data is encrypted and protected with military-grade security"
  },
  {
    icon: IconClock,
    title: "24/7 Availability",
    description: "Access medical guidance anytime, anywhere, without waiting"
  }
];

export default function Features() {
  return (
    <section className="py-24 px-4 bg-neutral-900">
      <div className="max-w-7xl mx-auto">
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8 }}
          className="text-center mb-16"
        >
          <h2 className="text-4xl font-bold text-white mb-6 font-serif">
            Why Choose Bluebox?
          </h2>
          <p className="text-xl text-gray-400 max-w-2xl mx-auto">
            Experience the future of healthcare with our cutting-edge AI technology
          </p>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {features.map((feature, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
              className="bg-neutral-800 p-6 rounded-2xl hover:bg-neutral-700 transition-colors"
            >
              <feature.icon className="w-12 h-12 text-blue-500 mb-4" />
              <h3 className="text-xl font-bold text-white mb-3">{feature.title}</h3>
              <p className="text-gray-400">{feature.description}</p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
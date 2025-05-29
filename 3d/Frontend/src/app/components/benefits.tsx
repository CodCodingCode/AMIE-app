'use client';

import { motion } from 'framer-motion';
import Image from 'next/image';

export default function Benefits() {
  return (
    <section className="py-24 px-4 bg-neutral-950">
      <div className="max-w-7xl mx-auto">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8 }}
          >
            <h2 className="text-4xl font-bold text-white mb-6 font-serif">
              Healthcare Made Simple
            </h2>
            <div className="space-y-6">
              <div className="flex items-start">
                <div className="flex-shrink-0 w-12 h-12 bg-blue-500/10 rounded-full flex items-center justify-center">
                  <span className="text-blue-500 text-2xl">1</span>
                </div>
                <div className="ml-4">
                  <h3 className="text-xl font-semibold text-white mb-2">Quick Consultation</h3>
                  <p className="text-gray-400">Get instant medical guidance without the wait times of traditional healthcare</p>
                </div>
              </div>
              
              <div className="flex items-start">
                <div className="flex-shrink-0 w-12 h-12 bg-blue-500/10 rounded-full flex items-center justify-center">
                  <span className="text-blue-500 text-2xl">2</span>
                </div>
                <div className="ml-4">
                  <h3 className="text-xl font-semibold text-white mb-2">Smart Analysis</h3>
                  <p className="text-gray-400">Our AI analyzes your symptoms and medical history for personalized care</p>
                </div>
              </div>
              
              <div className="flex items-start">
                <div className="flex-shrink-0 w-12 h-12 bg-blue-500/10 rounded-full flex items-center justify-center">
                  <span className="text-blue-500 text-2xl">3</span>
                </div>
                <div className="ml-4">
                  <h3 className="text-xl font-semibold text-white mb-2">Follow-up Care</h3>
                  <p className="text-gray-400">Receive ongoing support and monitoring for your health journey</p>
                </div>
              </div>
            </div>
          </motion.div>
          
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8 }}
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
'use client';

import { motion } from 'framer-motion';
import { useRouter } from 'next/navigation';

export default function CallToAction() {
  const router = useRouter();

  return (
    <section className="py-24 px-4 bg-neutral-950 relative overflow-hidden">
      {/* Background gradient effect */}
      <div className="absolute inset-0 bg-gradient-to-r from-blue-600/20 to-purple-600/20 opacity-50" />
      
      <div className="max-w-4xl mx-auto text-center relative z-10">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8 }}
        >
          <h2 className="text-5xl font-bold text-white mb-8 font-serif">
            Ready to Take Control of Your Health?
          </h2>
          <p className="text-xl text-gray-300 mb-12 max-w-2xl mx-auto">
            Join thousands of users who trust Bluebox for instant medical guidance and personalized healthcare support.
          </p>
          <button
            onClick={() => router.push('/chat')}
            className="bg-blue-600 text-white px-8 py-4 rounded-full text-lg font-semibold hover:bg-blue-700 transition-colors"
          >
            Start Your Free Consultation
          </button>
        </motion.div>
      </div>
    </section>
  );
}
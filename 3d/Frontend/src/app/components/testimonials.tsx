'use client';

import { motion } from 'framer-motion';
import Image from 'next/image';

const testimonials = [
  {
    name: "Sarah Johnson",
    role: "Patient",
    image: "https://images.pexels.com/photos/733872/pexels-photo-733872.jpeg",
    quote: "Bluebox has been a game-changer for managing my health. The instant access to medical guidance gives me peace of mind."
  },
  {
    name: "Dr. Michael Chen",
    role: "Healthcare Professional",
    image: "https://images.pexels.com/photos/5452293/pexels-photo-5452293.jpeg",
    quote: "As a doctor, I'm impressed by Bluebox's accuracy and ability to provide reliable preliminary medical guidance."
  },
  {
    name: "Emma Thompson",
    role: "Regular User",
    image: "https://images.pexels.com/photos/1239291/pexels-photo-1239291.jpeg",
    quote: "The convenience of having a medical AI assistant available 24/7 has made managing my family's health so much easier."
  }
];

export default function Testimonials() {
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
            What Our Users Say
          </h2>
          <p className="text-xl text-gray-400 max-w-2xl mx-auto">
            Join thousands of satisfied users who trust Bluebox for their healthcare needs
          </p>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {testimonials.map((testimonial, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
              className="bg-neutral-800 p-8 rounded-2xl"
            >
              <div className="flex items-center mb-6">
                <div className="relative w-16 h-16 rounded-full overflow-hidden">
                  <Image
                    src={testimonial.image}
                    alt={testimonial.name}
                    fill
                    className="object-cover"
                  />
                </div>
                <div className="ml-4">
                  <h3 className="text-lg font-semibold text-white">{testimonial.name}</h3>
                  <p className="text-gray-400">{testimonial.role}</p>
                </div>
              </div>
              <p className="text-gray-300 italic">"{testimonial.quote}"</p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
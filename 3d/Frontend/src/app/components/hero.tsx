'use client';

import PortalScene from '../portalcomps/portalcomplete';
import { motion } from 'framer-motion';

export default function Hero() {
  return (
    <section className="relative h-screen w-full overflow-hidden">
      {/* 3D Scene */}
      <PortalScene />
      
      {/* Overlay Content - Moved more to the right */}
      <div className="absolute top-0 left-0 h-full w-full flex items-center justify-start z-10 px-4 pointer-events-none">
        <div className="text-left ml-auto mr-auto" style={{ marginLeft: '5%', marginRight: 'auto' }}>
          <motion.h1 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="text-4xl md:text-6xl lg:text-7xl font-bold text-white mb-6 font-serif"
          >
            Your Personal AI Doctor
          </motion.h1>
          <motion.p 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.4 }}
            className="text-xl md:text-2xl text-gray-300 mb-8 max-w-md"
          >
            24/7 medical guidance powered by advanced AI technology
          </motion.p>
        </div>
      </div>

    </section>
  );
}
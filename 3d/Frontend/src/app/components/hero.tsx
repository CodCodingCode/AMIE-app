'use client';

import PortalScene from '../portalcomps/portalcomplete';
import { motion } from 'framer-motion';

export default function Hero() {
  return (
    <section className="relative h-screen w-full overflow-hidden">
      {/* 3D Scene */}
      <PortalScene />

    </section>
  );
}
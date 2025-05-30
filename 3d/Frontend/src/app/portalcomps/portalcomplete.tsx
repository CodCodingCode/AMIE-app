'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Canvas } from '@react-three/fiber';
import { PerspectiveCamera } from '@react-three/drei';
import * as THREE from 'three';
import Box3D from './Box3D';
import MouseParallax from './MouseParallax';
import BasicLights from './lights';
import { usePathname } from 'next/navigation';
import AnimatedStars from './stars';
import Platform from './cube';
import { motion } from 'framer-motion';

interface PortalSceneProps {}

const PortalScene = (props: PortalSceneProps) => {
  const [canvasResetKey, setCanvasResetKey] = useState(0);
  const [isZooming, setIsZooming] = useState(false);
  const [boxKey, setBoxKey] = useState(0);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const pathname = usePathname();

  useEffect(() => {
    if (pathname === '/') {
      setBoxKey(prevKey => prevKey + 1);
      setIsZooming(false);
    }
  }, [pathname]);

  useEffect(() => {
    const handleContextLost = (e: Event) => {
      e.preventDefault();
      setCanvasResetKey(prev => prev + 1);
    };
    const canvas = canvasRef.current;
    canvas?.addEventListener('webglcontextlost', handleContextLost);
    return () => canvas?.removeEventListener('webglcontextlost', handleContextLost);
  }, []);

  return (
    <div className="relative h-screen w-full bg-neutral-900">
      <Canvas 
        key={canvasResetKey}
        gl={{ antialias: true }}
        onCreated={({ gl }) => {
          canvasRef.current = gl.domElement;
          gl.toneMapping = THREE.ACESFilmicToneMapping;
          gl.toneMappingExposure = 1.5;
        }}
      >
        <PerspectiveCamera makeDefault position={[0, 0, 15]} fov={60} />
        <MouseParallax isEnabled={!isZooming} strength={0.5} dampingFactor={0.10} />
        <Box3D 
          key={boxKey} 
          onZoomStart={() => setIsZooming(true)} 
        />
        <BasicLights />
        <AnimatedStars />
      </Canvas>
      
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
    </div>
  );
};

export default PortalScene;
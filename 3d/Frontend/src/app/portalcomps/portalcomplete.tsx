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
import { useBlueboxAnimation } from '@/app/lib/hooks';

interface PortalSceneProps {}

const PortalScene = (props: PortalSceneProps) => {
  const [canvasResetKey, setCanvasResetKey] = useState(0);
  const [isZooming, setIsZooming] = useState(false);
  const [boxKey, setBoxKey] = useState(0);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const pathname = usePathname();
  const { isAnimationStarted, handleGetStartedClick } = useBlueboxAnimation();

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
        style={{ zIndex: 1 }}
      >
        <PerspectiveCamera makeDefault position={[0, 0, 15]} fov={60} />
        <MouseParallax isEnabled={!isZooming} strength={0.5} dampingFactor={0.10} />
        <Box3D 
          key={boxKey} 
          onZoomStart={() => setIsZooming(true)} 
          onBoxClicked={handleGetStartedClick}
        />
        <BasicLights />
        <AnimatedStars />
      </Canvas>

      {/* Hero Text Overlay - Now with hero-title-container class for targeting in animations */}
      <div 
        className={`hero-title-container absolute inset-0 flex items-center justify-start z-10 transition-opacity duration-500 ease-in-out pointer-events-none ${
          isAnimationStarted ? 'opacity-0' : 'opacity-100'
        }`}
      >
        <div className="text-center px-4 pl-16 pointer-events-none">
          <h1 className="text-4xl md:text-6xl lg:text-7xl font-bold text-white mb-6 font-serif">
            Your Personal AI Doctor
          </h1>
          <p className="text-xl md:text-2xl text-gray-300 mb-8 max-w-2xl mx-auto">
            24/7 medical guidance powered by advanced AI technology
          </p>
        </div>
      </div>
    </div>
  );
};

export default PortalScene;
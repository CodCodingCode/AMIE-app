'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Canvas } from '@react-three/fiber';
import { PerspectiveCamera, Text } from '@react-three/drei';
import * as THREE from 'three';
import { EffectComposer, Bloom, GodRays } from '@react-three/postprocessing';
import Box3D from './Box3D';
import MouseParallax from './MouseParallax';
import AnimatedStars from './stars';
import BasicLights from './lights';
import Platform from './cube';
import { BlendFunction, KernelSize } from 'postprocessing';

// Main component with canvas setup
const PortalScene = () => {
  const [key, setKey] = useState(0);
  const [isZooming, setIsZooming] = useState(false);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const sunRef = useRef<THREE.Mesh>(null!);

  // Handle WebGL context loss
  useEffect(() => {
    const handleContextLost = (e: Event) => {
      e.preventDefault();
      setKey(prev => prev + 1);
    };

    const canvas = canvasRef.current;
    canvas?.addEventListener('webglcontextlost', handleContextLost);
    return () => canvas?.removeEventListener('webglcontextlost', handleContextLost);
  }, []);

  return (
    <div className="h-screen w-full bg-black relative">
      <Canvas
        key={key}
        gl={{ antialias: true }}
        onCreated={({ gl }) => {
          canvasRef.current = gl.domElement;
          gl.toneMapping = THREE.ACESFilmicToneMapping;
          gl.toneMappingExposure = 1.5;
        }}
      >
        <PerspectiveCamera makeDefault position={[0, 0, 15]} fov={60} />
        
        {/* Scene Content */}
        <MouseParallax isEnabled={!isZooming} strength={0.5} dampingFactor={0.10} />
        
        {/* Platform beneath the box */}
        <Platform 
          position={[17, -37, -40]} 
          rotation={Math.PI * 2.25}
          width={24}
          height={50}
          length={40}
          color="#555555"
        />
        <Platform
          position={[12, -42, -35]}
          rotation={Math.PI * 2.25}
          width={24}
          height={50}
          length={40}
          color="#555555"
        />
        <Platform
          position={[7, -47, -30]}
          rotation={Math.PI * 2.25}
          width={24}
          height={50}
          length={40}
          color="#555555"
        />
        <Platform
          position={[2, -52, -25]}
          rotation={Math.PI * 2.25}
          width={24}
          height={50}
          length={40}
          color="#555555"
        />
        
        <Box3D onZoomStart={() => setIsZooming(true)} />
        <AnimatedStars />
        <BasicLights />

      <Text
        position={[-6.5, 0, 0]} // Adjust position to where you want the text
        fontSize={1}
        color="white"
        anchorX="center"
        anchorY="middle"
      >
        Enter the Bluebox
      </Text>
      </Canvas>
    </div>
  );
};

export default PortalScene; 
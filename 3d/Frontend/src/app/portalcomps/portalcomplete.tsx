'use client';

import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Canvas, useThree, useFrame } from '@react-three/fiber';
import {Stars, Preload, Text, PerspectiveCamera, OrbitControls} from '@react-three/drei';
import { useRouter } from 'next/navigation';
import { Group } from 'three';
import * as THREE from 'three';
import { EffectComposer, Bloom } from '@react-three/postprocessing';
import { Physics } from '@react-three/rapier';
import Box3D from './Box3D';
import MouseParallax from './MouseParallax';

// Background stars with subtle animation
const AnimatedStars = () => {
  const starsRef = useRef<Group>(null);
  useFrame(() => starsRef.current && (starsRef.current.rotation.y += 0.0005));
  
  return (
    <group ref={starsRef}>
      <Stars radius={40} depth={20} count={1000} factor={2} saturation={0.5} fade speed={0.3} />
    </group>
  );
};

// Scene lighting
const BasicLights = () => (
  <>
    <ambientLight intensity={0.4} color="#b9d5ff" />
    <directionalLight position={[5, 8, 5]} intensity={1.2} color="#ffffff" castShadow shadow-mapSize={256} />
    <directionalLight position={[-5, 3, 0]} intensity={0.5} color="#4d71ff" />
  </>
);

// Main scene content
const SceneContent = () => {
  const router = useRouter();
  const [isZooming, setIsZooming] = useState(false);
  
  const handleZoomComplete = useCallback(() => {
    router.push('/chat');
  }, [router]);
  
  // Create a handler to be notified when Box3D starts zooming
  const handleZoomStart = useCallback(() => {
    setIsZooming(true);
  }, []);
  
  return (
    <>
      <MouseParallax isEnabled={!isZooming} strength={0.5} dampingFactor={0.10} />
      <Physics>
        <Box3D onZoomComplete={handleZoomComplete} onZoomStart={handleZoomStart} />
      </Physics>
      <AnimatedStars />
      <BasicLights />
    </>
  );
};

// Main component with canvas setup
const PortalScene = () => {
  const [key, setKey] = useState(0);
  const canvasRef = useRef<HTMLCanvasElement>(null);

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
        <OrbitControls />
        <PerspectiveCamera makeDefault position={[0, 0, 15]} fov={60} />
        <SceneContent />
        <EffectComposer>
          <Bloom intensity={1.5} luminanceThreshold={0.2} luminanceSmoothing={0.9} mipmapBlur />
        </EffectComposer>
      </Canvas>
    </div>
  );
};

export default PortalScene; 
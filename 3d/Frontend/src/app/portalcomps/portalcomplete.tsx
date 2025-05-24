'use client';
import React, { useState, useRef, useEffect } from 'react';
import { Canvas } from '@react-three/fiber';
import { PerspectiveCamera, OrbitControls } from '@react-three/drei';
import * as THREE from 'three';
import Box3D from './Box3D';
import MouseParallax from './MouseParallax';
import BasicLights from './lights';
import { usePathname } from 'next/navigation';
import EnterText from './entertext';

// Main component with canvas setup
const PortalScene = () => {
  const [canvasResetKey, setCanvasResetKey] = useState(0);
  const [isZooming, setIsZooming] = useState(false);
  const [initiateTextFade, setInitiateTextFade] = useState(false);
  const [boxKey, setBoxKey] = useState(0);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const pathname = usePathname();

  useEffect(() => {
    if (pathname === '/') {
      setBoxKey(prevKey => prevKey + 1);
      setIsZooming(false);
      setInitiateTextFade(false);
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
    <div className="h-screen w-full bg-white relative">
      <Canvas 
        key={canvasResetKey}
        gl={{ 
          antialias: true
        }}
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
          onBoxClicked={() => setInitiateTextFade(true)}
        />
        
        <BasicLights />
        <EnterText 
          startFade={initiateTextFade} 
          position={[-6, 2, 0]}
          rotation={[Math.PI/2, 0, 0]}
          scale={1.05}
        />
      </Canvas>
    </div>
  );
};

export default PortalScene;
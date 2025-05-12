'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { 
  Stars, 
  useGLTF, 
  Preload,
  Text,
  PerspectiveCamera,
  OrbitControls
} from '@react-three/drei';
import { useRouter } from 'next/navigation';
import { 
  Mesh, 
  Group,
} from 'three';

// Preload the 3D model
useGLTF.preload('/boxattempt1.glb');

// Box 3D Model
const Box3D = ({ onZoomComplete }: { onZoomComplete: () => void }) => {
  const { scene } = useGLTF('/boxattempt1.glb');
  const boxRef = useRef<Group>(null);
  const [isZooming, setIsZooming] = useState(false);
  
  useEffect(() => {
    if (boxRef.current) {
      boxRef.current.rotation.y = Math.PI * 1.25;
    }
    
    return () => {
      // Cleanup GLTF scene
      scene.traverse(child => {
        if (child instanceof Mesh) {
          child.geometry?.dispose();
          if (Array.isArray(child.material)) {
            child.material.forEach(m => m.dispose());
          } else {
            child.material?.dispose();
          }
        }
      });
    };
  }, [scene]);

  const handleClick = () => {
    if (isZooming) return;
    setIsZooming(true);
  };

  return (
    <primitive 
      ref={boxRef}
      object={scene} 
      position={[3, 0, 0]} 
      scale={0.5} 
      onClick={handleClick}
      cursor="pointer"
    />
  );
};

// Simple lighting setup
const BasicLights = () => {
  return (
    <>
      <ambientLight intensity={0.4} color="#b9d5ff" />
      <directionalLight
        position={[5, 8, 5]}
        intensity={1.2}
        color="#ffffff"
        castShadow
        shadow-mapSize={256}  // Reduced shadow quality
      />
      <directionalLight 
        position={[-5, 3, 0]} 
        intensity={0.5} 
        color="#4d71ff"
      />
    </>
  );
};

// Animated stars component - optimized
const AnimatedStars = () => {
  const starsRef = useRef<Group>(null);

  useFrame(() => {
    if (starsRef.current) {
      starsRef.current.rotation.y += 0.0005;
    }
  });

  return (
    <group ref={starsRef}>
      <Stars radius={40} depth={20} count={1000} factor={2} saturation={0.5} fade speed={0.3} />
    </group>
  );
};

// Simplified floor component
const Floor = () => {
  return (
    <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -2, 0]}>
      <planeGeometry args={[30, 30]} />
      <meshStandardMaterial 
        color="#070b34" 
        transparent
        opacity={0.7}
        roughness={0.7}
      />
    </mesh>
  );
};

// Scene content component
const SceneContent = ({ setIsFadingOut }: { setIsFadingOut: (value: boolean) => void }) => {
  const router = useRouter();
  
  const handleZoomComplete = () => {
    // Trigger fade out effect
    setIsFadingOut(true);
    
    // Navigate directly to chat after fade animation
    setTimeout(() => {
      router.push('/chat');
    }, 800);
  };
  
  return (
    <>
      <Box3D onZoomComplete={handleZoomComplete} />
      <Floor />
      <AnimatedStars />
      <BasicLights />
      <Text
        position={[-4.5, 1.5, 0]} // ⬆️ Floating above the Box
        fontSize={0.4}  // Reduced font size
        color="#ffffff"
        anchorX="center"
        anchorY="middle"
        characters="abcdefghijklmnopqrstuvwxyz0123456789!➡"  // Limited character set
      >
        Enter the Bluebox ➡
      </Text>
    </>
  );
};

// The main scene component with improved WebGL context handling
const PortalScene = () => {
  const [isFadingOut, setIsFadingOut] = useState(false);
  const [key, setKey] = useState(0);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const handleContextLost = (e: Event) => {
      e.preventDefault();
      console.log('Context lost, reloading scene...');
      setKey(prev => prev + 1);
    };

    const canvas = canvasRef.current;
    if (canvas) {
      canvas.addEventListener('webglcontextlost', handleContextLost, false);
    }

    return () => {
      if (canvas) {
        canvas.removeEventListener('webglcontextlost', handleContextLost, false);
      }
    };
  }, []);

  return (
    <div className="h-screen w-full bg-black relative">
      <Canvas 
        key={key}
        onCreated={({ gl }) => {
          canvasRef.current = gl.domElement;
        }}
      >
        <OrbitControls />
        <PerspectiveCamera makeDefault position={[0, 0, 10]} fov={75} />
        <fog attach="fog" args={['#070b34', 10, 30]} />
        <SceneContent setIsFadingOut={setIsFadingOut} />
        <Preload all />
      </Canvas>
      
      {/* Overlay for transition effect */}
      <div 
        className={`fixed inset-0 bg-white z-50 pointer-events-none transition-opacity duration-1000 ease-in-out ${isFadingOut ? 'opacity-100' : 'opacity-0'}`}
      />
    </div>
  );
};

export default PortalScene;
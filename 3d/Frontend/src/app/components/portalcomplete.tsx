'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { 
  PerspectiveCamera, 
  Stars, 
  useGLTF, 
  Preload,
  Text
} from '@react-three/drei';
import { useRouter } from 'next/navigation';
import { 
  Mesh, 
  Group
} from 'three';

// Preload the 3D model
useGLTF.preload('/boxattempt1.glb');

// Box 3D Model
const Box3D = ({ onClick }: { onClick?: () => void }) => {
  const { scene } = useGLTF('/boxattempt1.glb');
  const boxRef = useRef<Group>(null);
  
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

  useFrame(({ clock }) => {
    if (boxRef.current) {
      boxRef.current.position.y = Math.sin(clock.getElapsedTime() * 0.3) * 0.1;
      boxRef.current.rotation.y = Math.PI * 1.25 + Math.sin(clock.getElapsedTime() * 0.1) * 0.05;
    }
  });

  return (
    <primitive 
      ref={boxRef}
      object={scene} 
      position={[3, 0, 0]} 
      scale={0.5} 
      onClick={onClick}
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
        shadow-mapSize={512}
      />
      <directionalLight 
        position={[-5, 3, 0]} 
        intensity={0.5} 
        color="#4d71ff"
      />
    </>
  );
};

// Animated stars component
const AnimatedStars = () => {
  const starsRef = useRef<Group>(null);

  useFrame(() => {
    if (starsRef.current) {
      starsRef.current.rotation.y += 0.0005;
    }
  });

  return (
    <group ref={starsRef}>
      <Stars radius={50} depth={30} count={2000} factor={3} saturation={0.5} fade speed={0.5} />
    </group>
  );
};

// Floor to catch shadows
const Floor = () => {
  return (
    <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -2, 0]}>
      <planeGeometry args={[50, 50]} />
      <meshStandardMaterial 
        color="#070b34" 
        transparent
        opacity={0.7}
        roughness={0.7} 
        metalness={0.1}
      />
    </mesh>
  );
};

// Scene content component
const SceneContent = () => {
  const router = useRouter();
  
  const handlePortalClick = () => {
    try {
      router.push('/loading');
    } catch (error) {
      console.error("Navigation error:", error);
      window.location.href = '/loading';
    }
  };
  
  return (
    <>
      <Box3D onClick={handlePortalClick} />
      <Floor />
      <AnimatedStars />
      <BasicLights />
      <Text
        position={[-4.5, 1.5, 0]} // ⬆️ Floating above the Box
        fontSize={0.5}
        color="#ffffff"
        anchorX="center"
        anchorY="middle"
      >
        Enter the Bluebox ➡
      </Text>
    </>
  );
};

// The main scene component
const PortalScene = () => {
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
    <div className="h-screen w-full bg-black">
      <Canvas
        key={key}
        shadows
        gl={{
          antialias: true,
          powerPreference: "high-performance",
          preserveDrawingBuffer: true
        }}
        // Add event handlers to the underlying canvas element
        onCreated={({ gl }) => {
          canvasRef.current = gl.domElement;
        }}
      >
        <PerspectiveCamera makeDefault position={[0, 0, 10]} fov={75} />
        <fog attach="fog" args={['#070b34', 10, 50]} />
        <SceneContent />
        <Preload all />
      </Canvas>
    </div>
  );
};

export default PortalScene;
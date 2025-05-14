'use client';

import React, { useState, useRef, useEffect, createContext, useContext, useCallback, useMemo } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import {Stars, useGLTF, Preload, Text, PerspectiveCamera} from '@react-three/drei';
import { useRouter } from 'next/navigation';
import { Mesh, Group } from 'three';
import * as THREE from 'three';
import { EffectComposer, Bloom } from '@react-three/postprocessing';
import gsap from 'gsap';

useGLTF.preload('/bluebox1.glb');

// Simplified context with essential zoom state
const ZoomContext = createContext<{
  isZooming: boolean; 
  setIsZooming: (value: boolean) => void;
  handleZoom: () => void;
}>({
  isZooming: false,
  setIsZooming: () => {},
  handleZoom: () => {}
});

// Provider for zoom state and communication
const ZoomProvider = ({ children, onZoomComplete }: { children: React.ReactNode, onZoomComplete: () => void }) => {
  const [isZooming, setIsZooming] = useState(false);
  const { camera } = useThree();
  
  // Direct zoom handler in the provider
  const handleZoom = useCallback(() => {
    if (isZooming) return;
    setIsZooming(true);
  
    const tl = gsap.timeline({
      onComplete: onZoomComplete,
    });
  
    // Step 1: Move camera to target location
    tl.to(camera.position, {
      x: -40, y: 1, z: 20,
      duration: 1,
      ease: "power2.inOut",
    }, 0);
  
    // Step 2: Rotate camera
    tl.to(camera.rotation, {
      x: 0,
      y: -Math.PI / 4,
      z: 0,
      duration: 1,
      ease: "power2.inOut",
    }, 0);
  
    // Step 3: Zoom in (move camera closer)
    tl.to(camera.position, {
      x: 15, y: 0, z: -35,
      duration: 1,
      ease: "power2.inOut",
    }, "+=0");
  
  }, [camera, isZooming, onZoomComplete, setIsZooming]);

  // Simpler context value
  const contextValue = useMemo(() => ({
    isZooming,
    setIsZooming,
    handleZoom
  }), [isZooming, handleZoom]);

  return <ZoomContext.Provider value={contextValue}>{children}</ZoomContext.Provider>;
};

// Camera controller with simplified zoom handling
const CameraController = () => {
  const { camera } = useThree();
  const [mousePos, setMousePos] = useState([0, 0]);
  const { isZooming } = useContext(ZoomContext);

  // Handle mouse movement
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      setMousePos([
        (e.clientX / window.innerWidth) * 2 - 1,
        (e.clientY / window.innerHeight) * 2 - 1
      ]);
    };

    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);

  // Apply mouse effect to camera
  useFrame(() => {
    if (isZooming) return;
  
    camera.position.x += (mousePos[0] * 0.5 - camera.position.x) * 0.10;
    camera.position.y += (-mousePos[1] * 0.5 - camera.position.y) * 0.10;
    camera.lookAt(0, 0, 0);
  });

  return null;
};

// Interactive 3D box
const Box3D = ({ initialPosition = [30, 0, 0] }: { initialPosition?: [number, number, number] }) => {
  const { scene } = useGLTF('/bluebox1.glb');
  const boxRef = useRef<Group>(null);
  const materialRefs = useRef<THREE.MeshStandardMaterial[]>([]);
  const [isHovered, setIsHovered] = useState(false);
  const initialRotation = useRef(Math.PI * 2.25);
  const { isZooming, handleZoom } = useContext(ZoomContext);

  // Initialize box and handle cleanup
  useEffect(() => {
    if (!boxRef.current) return;
    
    // Set initial position and rotation
    boxRef.current.rotation.y = initialRotation.current;
    boxRef.current.position.set(...initialPosition);

    // Setup materials
    scene.traverse((child) => {
      if (child instanceof Mesh && child.material) {
        const mat = child.material as THREE.MeshStandardMaterial;
        mat.emissive = new THREE.Color(0x000000);
        mat.emissiveIntensity = 0;
        materialRefs.current.push(mat);
      }
    });

    // Cleanup
    return () => {
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
  }, [scene, initialPosition]);

  // Animate box based on hover state
  useFrame((state) => {
    if (!boxRef.current || isZooming) return;

    // Handle position, material, and rotation updates
    const box = boxRef.current;
    const { clock } = state;
    
    // Position animation
    box.position.y += ((isHovered ? 0.3 : 0) - box.position.y) * 0.1;
    
    // Material animation
    materialRefs.current.forEach((mat) => {
      if (isHovered) mat.emissive.set('#3daef5');
      mat.emissiveIntensity += ((isHovered ? 1.5 : 0) - mat.emissiveIntensity) * 0.1;
    });
    
    // Rotation animation
    if (isHovered) {
      box.rotation.y = initialRotation.current + Math.sin(clock.elapsedTime * 2) * 0.05;
      box.rotation.z = Math.sin(clock.elapsedTime * 1.5) * 0.02;
    } else {
      box.rotation.y += (initialRotation.current - box.rotation.y) * 0.1;
      box.rotation.z += (0 - box.rotation.z) * 0.1;
    }
    
    box.updateWorldMatrix(true, true);
  });

  return (
    <primitive
      ref={boxRef}
      object={scene}
      scale={8.0}
      onClick={handleZoom}
      onPointerOver={() => setIsHovered(true)}
      onPointerOut={() => setIsHovered(false)}
      cursor="pointer"
    />
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

// Main scene content
const SceneContent = () => {
  const router = useRouter();
  
  return (
    <ZoomProvider onZoomComplete={() => router.push('/chat')}>
      <CameraController />
      <Box3D />
      <AnimatedStars />
      <BasicLights />
      <Text
        position={[-4.5, 1.5, 0]}
        fontSize={0.4}
        color="#ffffff"
        anchorX="center"
        anchorY="middle"
      >
        Enter the Bluebox ➡
      </Text>
    </ZoomProvider>
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
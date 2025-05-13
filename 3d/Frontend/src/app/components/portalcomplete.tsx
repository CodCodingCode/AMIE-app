'use client';

import React, { useState, useRef, useEffect, useMemo } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import {
  Stars,
  useGLTF,
  Preload,
  Text,
  PerspectiveCamera,
  Grid,
  useHelper,
  OrbitControls,
} from '@react-three/drei';
import { useRouter } from 'next/navigation';
import {
  Mesh,
  Group,
  DirectionalLight,
  DirectionalLightHelper,
  Vector3,
} from 'three';
import * as THREE from 'three';
import FakeGlowMaterial from './fakeglowmaterial';

{/* Parallax Code */}
const CameraMouseEffect = () => {
  const { camera } = useThree();
  const [mousePos, setMousePos] = useState([0, 0]);
  
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      // Convert mouse position to normalized coordinates (-1 to 1)
      const x = (e.clientX / window.innerWidth) * 2 - 1;
      const y = (e.clientY / window.innerHeight) * 2 - 1;
      setMousePos([x, y]);
    };
    
    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);
  
  useFrame(() => {
    // Apply subtle tilt based on mouse position
    camera.position.x += (mousePos[0] * 0.5 - camera.position.x) * 0.10;
    camera.position.y += (-mousePos[1] * 0.5 - camera.position.y) * 0.10;
    camera.lookAt(0, 0, 0); // Always look at the center
  });
  
  return null;
};

useGLTF.preload('/boxattempt1.glb');

const Box3D = ({ onZoomComplete, initialPosition = [4, 0, 0] }: { onZoomComplete: () => void, initialPosition?: [number, number, number] }) => {
  const { scene } = useGLTF('/boxattempt1.glb');
  const boxRef = useRef<Group>(null);
  const [isZooming, setIsZooming] = useState(false);
  const [isHovered, setIsHovered] = useState(false);
  const initialRotation = useRef(Math.PI * 1.25);
  
  // Glowing toruses that will appear on hover
  const torus1Ref = useRef<Mesh>(null);
  const torus2Ref = useRef<Mesh>(null);
  const torus3Ref = useRef<Mesh>(null);
  
  useEffect(() => {
    if (boxRef.current) {
      boxRef.current.rotation.y = initialRotation.current;
      boxRef.current.position.set(initialPosition[0], initialPosition[1], initialPosition[2]);
    }

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

  useFrame((state) => {
    if (!boxRef.current) return;

    boxRef.current.updateWorldMatrix(true, true);

    const targetY = isHovered ? 0.3 : 0;
    boxRef.current.position.y += (targetY - boxRef.current.position.y) * 0.1;

    // Update all torus references when hovered
    const time = state.clock.getElapsedTime();
    
    // Only show and animate glowing toruses when hovered
    if (torus1Ref.current && torus2Ref.current && torus3Ref.current) {
      // Set all torus positions to match the box
      const boxPosition = new Vector3();
      if (boxRef.current) {
        boxRef.current.getWorldPosition(boxPosition);
        
        // First torus - horizontal around the middle
        torus1Ref.current.position.copy(boxPosition);
        torus1Ref.current.rotation.x = Math.PI / 2;
        torus1Ref.current.rotation.y += 0.005;
        torus1Ref.current.scale.setScalar(isHovered ? 0.9 + Math.sin(time * 2) * 0.05 : 0.01);
        
        // Second torus - vertical around the box
        torus2Ref.current.position.copy(boxPosition);
        torus2Ref.current.rotation.y += 0.008;
        torus2Ref.current.scale.setScalar(isHovered ? 0.85 + Math.sin(time * 1.5 + 1) * 0.05 : 0.01);
        
        // Third torus - at an angle
        torus3Ref.current.position.copy(boxPosition);
        torus3Ref.current.rotation.x = Math.PI / 4;
        torus3Ref.current.rotation.z += 0.006;
        torus3Ref.current.scale.setScalar(isHovered ? 0.95 + Math.sin(time * 1.8 + 2) * 0.05 : 0.01);
      }
    }

    if (isHovered) {
      boxRef.current.rotation.y = initialRotation.current + Math.sin(state.clock.elapsedTime * 2) * 0.05;
      boxRef.current.rotation.z = Math.sin(state.clock.elapsedTime * 1.5) * 0.02;
    } else {
      boxRef.current.rotation.y += (initialRotation.current - boxRef.current.rotation.y) * 0.1;
      boxRef.current.rotation.z += (0 - boxRef.current.rotation.z) * 0.1;
    }
  });

  const handleClick = () => {
    if (isZooming) return;
    setIsZooming(true);
    onZoomComplete();
  };

  // Create torus geometries with different parameters for variety
  const torus1Geometry = useMemo(() => new THREE.TorusGeometry(1.2, 0.08, 16, 100), []);
  const torus2Geometry = useMemo(() => new THREE.TorusGeometry(1.3, 0.06, 16, 100), []);
  const torus3Geometry = useMemo(() => new THREE.TorusGeometry(1.25, 0.07, 16, 100), []);

  return (
    <group>
      {/* First glowing torus - horizontal */}
      <mesh ref={torus1Ref} scale={0.5} position={initialPosition}>
        <primitive object={torus1Geometry} />
        <FakeGlowMaterial 
          glowColor="#51a4de" 
          falloff={0.2}
          glowInternalRadius={6.0}
          glowSharpness={1.2}
          opacity={0.8}
        />
      </mesh>

      {/* Second glowing torus - vertical */}
      <mesh ref={torus2Ref} scale={0.5} position={initialPosition}>
        <primitive object={torus2Geometry} />
        <FakeGlowMaterial 
          glowColor="#36ccf5" 
          falloff={0.15}
          glowInternalRadius={5.5}
          glowSharpness={1.0}
          opacity={0.8}
        />
      </mesh>

      {/* Third glowing torus - angled */}
      <mesh ref={torus3Ref} scale={0.5} position={initialPosition}>
        <primitive object={torus3Geometry} />
        <FakeGlowMaterial 
          glowColor="#2a7de8" 
          falloff={0.18}
          glowInternalRadius={5.8}
          glowSharpness={1.1}
          opacity={0.8}
        />
      </mesh>

      {/* Original box model */}
      <primitive
        ref={boxRef}
        object={scene}
        scale={0.5}
        onClick={handleClick}
        onPointerOver={() => setIsHovered(true)}
        onPointerOut={() => setIsHovered(false)}
        cursor="pointer"
      />
    </group>
  );
};

const BasicLights = () => {
  const directionalLight1Ref = useRef<DirectionalLight>(null!);
  const directionalLight2Ref = useRef<DirectionalLight>(null!);

  useHelper(directionalLight1Ref, DirectionalLightHelper, 1, 'red');
  useHelper(directionalLight2Ref, DirectionalLightHelper, 1, 'blue');

  return (
    <>
      <ambientLight intensity={0.4} color="#b9d5ff" />
      <directionalLight
        ref={directionalLight1Ref}
        position={[5, 8, 5]}
        intensity={1.2}
        color="#ffffff"
        castShadow
        shadow-mapSize={256}
      />
      <directionalLight 
        ref={directionalLight2Ref}
        position={[-5, 3, 0]} 
        intensity={0.5} 
        color="#4d71ff"
      />
      <Grid 
        infiniteGrid 
        cellSize={1} 
        cellThickness={0.5} 
        sectionSize={3} 
        sectionThickness={1}
        fadeDistance={30}
        fadeStrength={1}
      />
    </>
  );
};

const AnimatedStars = () => {
  const starsRef = useRef<Group>(null);
  useFrame(() => starsRef.current && (starsRef.current.rotation.y += 0.0005));
  return (
    <group ref={starsRef}>
      <Stars radius={40} depth={20} count={1000} factor={2} saturation={0.5} fade speed={0.3} />
    </group>
  );
};

const SceneContent = () => {
  const router = useRouter();

  const animateCamera = async () => {
    router.push('/chat');
  };

  return (
    <>
      <CameraMouseEffect />
      <Box3D onZoomComplete={animateCamera} />
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
    </>
  );
};

const PortalScene = () => {
  const [key, setKey] = useState(0);
  const canvasRef = useRef<HTMLCanvasElement>(null);

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
          gl.toneMappingExposure = 1.0;
        }}
      >
        <PerspectiveCamera makeDefault position={[0, 0, 10]} fov={75} />
        <fog attach="fog" args={['#070b34', 10, 30]} />
        <SceneContent />
        <Preload all />
      </Canvas>
    </div>
  );
};

export default PortalScene;


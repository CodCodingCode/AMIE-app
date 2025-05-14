'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import {
  Stars,
  useGLTF,
  Preload,
  Text,
  PerspectiveCamera,
  useHelper,
} from '@react-three/drei';
import { useRouter } from 'next/navigation';
import {
  Mesh,
  Group,
  DirectionalLight,
  DirectionalLightHelper,
} from 'three';
import * as THREE from 'three';
import { EffectComposer, Bloom } from '@react-three/postprocessing';

const CameraMouseEffect = () => {
  const { camera } = useThree();
  const [mousePos, setMousePos] = useState([0, 0]);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      const x = (e.clientX / window.innerWidth) * 2 - 1;
      const y = (e.clientY / window.innerHeight) * 2 - 1;
      setMousePos([x, y]);
    };

    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);

  useFrame(() => {
    camera.position.x += (mousePos[0] * 0.5 - camera.position.x) * 0.10;
    camera.position.y += (-mousePos[1] * 0.5 - camera.position.y) * 0.10;
    camera.lookAt(0, 0, 0);
  });

  return null;
};

useGLTF.preload('/boxattempt1.glb');

const Box3D = ({ onZoomComplete, initialPosition = [4, 0, 0] }: { onZoomComplete: () => void, initialPosition?: [number, number, number] }) => {
  const { scene } = useGLTF('/boxattempt1.glb');
  const boxRef = useRef<Group>(null);
  const materialRefs = useRef<THREE.MeshStandardMaterial[]>([]);
  const [isZooming, setIsZooming] = useState(false);
  const [isHovered, setIsHovered] = useState(false);
  const initialRotation = useRef(Math.PI * 1.25);

  useEffect(() => {
    if (boxRef.current) {
      boxRef.current.rotation.y = initialRotation.current;
      boxRef.current.position.set(initialPosition[0], initialPosition[1], initialPosition[2]);
    }

    scene.traverse((child) => {
      if (child instanceof Mesh && child.material) {
        const mat = child.material as THREE.MeshStandardMaterial;
        mat.emissive = new THREE.Color(0x000000);
        mat.emissiveIntensity = 0;
        materialRefs.current.push(mat);
      }
    });

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

    // Emissive glow effect
    materialRefs.current.forEach((mat) => {
      if (isHovered) {
        mat.emissive = new THREE.Color('#3daef5');
        mat.emissiveIntensity += (1.5 - mat.emissiveIntensity) * 0.1;
      } else {
        mat.emissiveIntensity += (0 - mat.emissiveIntensity) * 0.1;
      }
    });

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

  return (
    <group>
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
          gl.toneMappingExposure = 1.5;
        }}
      >
        <PerspectiveCamera makeDefault position={[0, 0, 10]} fov={75} />
        <fog attach="fog" args={['#070b34', 10, 30]} />
        <SceneContent />

        {/* 🌟 Add bloom effect */}
        <EffectComposer>
          <Bloom
            intensity={1.5}
            luminanceThreshold={0.2}
            luminanceSmoothing={0.9}
            mipmapBlur
          />
        </EffectComposer>

        <Preload all />
      </Canvas>
    </div>
  );
};

export default PortalScene;
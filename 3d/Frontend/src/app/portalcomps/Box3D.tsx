import React, { useState, useRef, useEffect, createRef } from 'react';
import { useFrame, useThree } from '@react-three/fiber';
import { useGLTF } from '@react-three/drei';
import { Mesh, Group, Vector3, Plane } from 'three';
import * as THREE from 'three';
import gsap from 'gsap';

// Preload models
useGLTF.preload('/blueboxreal.glb');

type Box3DProps = {
  initialPosition?: [number, number, number];
  onZoomComplete?: () => void;
  onZoomStart?: () => void;
};

// Interactive 3D box
const Box3D = ({ initialPosition = [30, 0, 0], onZoomComplete, onZoomStart }: Box3DProps) => {
  const { scene } = useGLTF('/blueboxreal.glb');
  const boxRef = useRef<Group>(null);
  const materialRefs = useRef<THREE.MeshStandardMaterial[]>([]);
  const [isHovered, setIsHovered] = useState(false);
  const [isZooming, setIsZooming] = useState(false);
  const initialRotation = useRef(Math.PI * 2.25);
  const { camera } = useThree();
  
  // References for sliding doors
  const leftDoorRef = useRef<Mesh | null>(null);
  const rightDoorRef = useRef<Mesh | null>(null);
  const logoOuterRef = useRef<Mesh | null>(null);
  const logoInnerRef = useRef<Mesh | null>(null);
  
  // Store initial positions of doors
  const leftDoorInitialPos = useRef<THREE.Vector3 | null>(null);
  const rightDoorInitialPos = useRef<THREE.Vector3 | null>(null);
  const logoOuterInitialPos = useRef<THREE.Vector3 | null>(null);
  const logoInnerInitialPos = useRef<THREE.Vector3 | null>(null);

  // Initialize box and handle cleanup
  useEffect(() => {
    if (!boxRef.current) return;
    
    // Set initial position and rotation
    boxRef.current.rotation.y = initialRotation.current;
    boxRef.current.position.set(...initialPosition);

    // Find and set up sliding doors
    scene.traverse((child) => {
      if (child instanceof Mesh) {
        // Store references to specific doors
        if (child.name === 'Cube') {
          leftDoorRef.current = child;
          leftDoorInitialPos.current = child.position.clone();
        } else if (child.name === 'Cube003') {
          rightDoorRef.current = child;
          rightDoorInitialPos.current = child.position.clone();
        } else if (child.name === 'Curve') {
          logoOuterRef.current = child;
          logoOuterInitialPos.current = child.position.clone();
        } else if (child.name === 'Curve001') {
          logoInnerRef.current = child;
          logoInnerInitialPos.current = child.position.clone();
        }
        
        // Setup materials for all meshes
        if (child.material) {
          const mat = child.material as THREE.MeshStandardMaterial;
          mat.emissive = new THREE.Color(0x000000);
          mat.emissiveIntensity = 0;
          materialRefs.current.push(mat);
        }
      }
    });
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
  });

  // Handle both door opening and camera zoom animations
  const handleZoom = () => {
    if (isZooming) return;
    
    // Set zooming state
    setIsZooming(true);
    
    // Notify parent component that zooming has started
    if (onZoomStart) {
      onZoomStart();
    }
    
    // Create a single timeline for all animations
    const tl = gsap.timeline({
      onComplete: () => {
        // Call the provided callback when animation is complete
        if (onZoomComplete) {
          onZoomComplete();
        }
      }
    });
    
    // Add door animations if doors exist
    if (leftDoorRef.current && rightDoorRef.current && 
        leftDoorInitialPos.current && rightDoorInitialPos.current) {
      
      const leftOpenOffset = new THREE.Vector3(0, 0, -0.6);
      const rightOpenOffset = new THREE.Vector3(0, 0, 0.6);
      
      // Door animations
      tl.to(leftDoorRef.current.position, {
        z: leftDoorInitialPos.current.z + leftOpenOffset.z,
        duration: 0.8,
        ease: "power2.out"
      }, 0);
      
      tl.to(rightDoorRef.current.position, {
        z: rightDoorInitialPos.current.z + rightOpenOffset.z,
        duration: 0.8,
        ease: "power2.out"
      }, 0);
      
      // Logo animations
      if (logoOuterRef.current && logoOuterInitialPos.current) {
        tl.to(logoOuterRef.current.position, {
          y: logoOuterInitialPos.current.y + 0.1,
          duration: 0.8,
          ease: "power2.out"
        }, 0);
        
        const matOuter = logoOuterRef.current.material as THREE.MeshStandardMaterial;
        tl.to(matOuter, {
          opacity: 0,
          duration: 0.8,
          ease: "power2.out",
          onUpdate: () => {
            if (matOuter.transparent === false) {
              matOuter.transparent = true;
            }
          }
        }, 0);
      }
      
      if (logoInnerRef.current && logoInnerInitialPos.current) {
        tl.to(logoInnerRef.current.position, {
          y: logoInnerInitialPos.current.y + 0.2,
          duration: 0.8,
          ease: "power2.out"
        }, 0);
        
        const matInner = logoInnerRef.current.material as THREE.MeshStandardMaterial;
        tl.to(matInner, {
          opacity: 0,
          duration: 0.8,
          ease: "power2.out",
          onUpdate: () => {
            if (matInner.transparent === false) {
              matInner.transparent = true;
            }
          }
        }, 0);
      }
    }
    
    // Camera animation
    tl.to(camera.position, {
      x: -40, y: 1, z: 20,
      duration: 1,
      ease: "power2.inOut",
    }, 0);
    
    tl.to(camera.rotation, {
      x: 0,
      y: -Math.PI / 4,
      z: 0,
      duration: 1,
      ease: "power2.inOut", 
    }, 0);
    
    tl.to(camera.position, {
      x: 15, y: 0, z: -35,
      duration: 1,
      ease: "power2.inOut",
    }, "+=0");
  };

  return (
    <>
      <primitive
        ref={boxRef}
        object={scene}
        scale={8.0}
        onClick={handleZoom}
        onPointerOver={() => setIsHovered(true)}
        onPointerOut={() => setIsHovered(false)}
        cursor="pointer"
      />
    </>
  );
};

export default Box3D; 
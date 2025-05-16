import React, { useRef, useEffect } from 'react';
import { useFrame, useThree } from '@react-three/fiber';
import { useGLTF } from '@react-three/drei';
import { Mesh, Group } from 'three';
import * as THREE from 'three';
import gsap from 'gsap';
import { useRouter } from 'next/navigation';

type Box3DProps = {
  initialPosition?: [number, number, number];
  onZoomStart?: () => void;
};

// Interactive 3D box
const Box3D = ({ initialPosition = [30, 0, 0], onZoomStart }: Box3DProps) => {
  const router = useRouter();
  const { scene } = useGLTF('/blueboxreal.glb');
  const boxRef = useRef<Group>(null);
  const materialRefs = useRef<THREE.MeshStandardMaterial[]>([]);
  const initialRotation = useRef(Math.PI * 2.25);
  const { camera } = useThree();
  const isHovered = useRef(false);
  const isZooming = useRef(false);
  
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
    boxRef.current.position.set(initialPosition[0], initialPosition[1], initialPosition[2]);

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
    if (!boxRef.current || isZooming.current) return;

    // Handle position, material, and rotation updates
    const box = boxRef.current;
    
    // Position animation
    box.position.y += ((isHovered.current ? 3 : 0) - box.position.y) * 0.1;
    
  });

  // Handle both door opening and camera zoom animations
  const handleZoom = () => {
    if (isZooming.current) return;
    isZooming.current = true;
    
    // Notify parent component that zooming has started (if provided)
    if (onZoomStart) {
      onZoomStart();
    }
    
    // Create a single timeline for all animations
    const tl = gsap.timeline({
      onComplete: () => {
        // Just navigate directly
        router.push('/chat');
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
      
      // Logo animations - combined for inner and outer logo
      if (logoOuterRef.current && logoInnerRef.current && 
          logoOuterInitialPos.current && logoInnerInitialPos.current) {
        
        // Animate both logo positions
        tl.to(logoOuterRef.current.position, {
          y: logoOuterInitialPos.current.y + 0.1,
          duration: 0.8,
          ease: "power2.out"
        }, 0);
        
        tl.to(logoInnerRef.current.position, {
          y: logoInnerInitialPos.current.y + 0.2,
          duration: 0.8,
          ease: "power2.out"
        }, 0);
        
        // Fade out both logo materials
        const matOuter = logoOuterRef.current.material as THREE.MeshStandardMaterial;
        const matInner = logoInnerRef.current.material as THREE.MeshStandardMaterial;
        
        [matOuter, matInner].forEach(mat => {
          tl.to(mat, {
            opacity: 0,
            duration: 0.8,
            ease: "power2.out",
            onUpdate: () => {
              if (mat.transparent === false) {
                mat.transparent = true;
              }
            }
          }, 0);
        });
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
        onPointerOver={() => { isHovered.current = true; }}
        onPointerOut={() => { isHovered.current = false; }}
        cursor="pointer"
      />
    </>
  );
};

export default Box3D; 
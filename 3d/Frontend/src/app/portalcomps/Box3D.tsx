import React, { useRef, useEffect, useMemo } from 'react';
import { useFrame, useThree } from '@react-three/fiber';
import { useGLTF } from '@react-three/drei';
import { Mesh, Group } from 'three';
import * as THREE from 'three';
import gsap from 'gsap';
import { useRouter } from 'next/navigation';

type Box3DProps = {
  initialPosition?: [number, number, number];
  onZoomStart?: () => void;
  onBoxClicked?: () => void;
  getTextAnimationControls?: () => any;
};

const Box3D = ({ initialPosition = [0, 0, -30], onZoomStart, onBoxClicked, getTextAnimationControls }: Box3DProps) => {
  const router = useRouter();
  const gltf = useGLTF('/blueboxrealagain.glb');

  const scene = useMemo(() => gltf.scene.clone(true), [gltf.scene]);

  const boxRef = useRef<Group>(null);
  const materialRefs = useRef<THREE.MeshStandardMaterial[]>([]);
  const initialRotation = useRef(Math.PI * 2.25);
  const { camera } = useThree();
  const isHovered = useRef(false);
  const isZooming = useRef(false);
  const leftDoorRef = useRef<Mesh | null>(null);
  const rightDoorRef = useRef<Mesh | null>(null);
  const logoOuterRef = useRef<Mesh | null>(null);
  const logoInnerRef = useRef<Mesh | null>(null);

  const cube005Ref = useRef<Mesh | null>(null);
  const cube005MaterialRef = useRef<THREE.MeshStandardMaterial | null>(null);

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

    // Reset all refs
    leftDoorRef.current = null;
    rightDoorRef.current = null;
    logoOuterRef.current = null;
    logoInnerRef.current = null;
    cube005Ref.current = null;
    cube005MaterialRef.current = null;
    leftDoorInitialPos.current = null;
    rightDoorInitialPos.current = null;
    logoOuterInitialPos.current = null;
    logoInnerInitialPos.current = null;
    materialRefs.current = [];

    // Find and set up sliding doors and materials
    scene.traverse((child) => {
      if (child instanceof Mesh && child.material) {
        const mat = child.material as THREE.MeshStandardMaterial;

        // Reset default material state
        mat.emissive = new THREE.Color("#171717");
        mat.emissiveIntensity = 0;
        mat.opacity = 1.0;
        mat.transparent = false;

        // Store references to specific doors and objects
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
        } else if (child.name === 'Cube005') {
          cube005Ref.current = child;
          cube005MaterialRef.current = mat;

          // Make Cube005 emissive black - creates a dark glow effect
          mat.color = new THREE.Color(0x000000); // Set base color to black
          mat.emissive = new THREE.Color(0x000000); // Black emissive color
          mat.emissiveIntensity = 1.5; // Intensity for the dark glow
          mat.metalness = 0.1; // Reduce metalness for better emissive effect
          mat.roughness = 0.8; // Increase roughness for softer appearance
        }

        materialRefs.current.push(mat);
      }
    });
  }, [scene, initialPosition]);

  useFrame(() => {
    if (!boxRef.current || isZooming.current) return;
    const box = boxRef.current;

    // Hover-based lift animation
    box.position.y += ((isHovered.current ? 3 : 0) - box.position.y) * 0.1;
  });

  const handleZoom = () => {
    if (isZooming.current) return;
    isZooming.current = true;

    if (onBoxClicked) {
      onBoxClicked();
    }

    window.scrollTo({ top: 0, behavior: 'smooth' });

    setTimeout(() => {
      if (onZoomStart) onZoomStart();

      const tl = gsap.timeline({
        onComplete: () => {
          router.push('/chat');
        }
      });

      // Fade out the enter text if available
      if (getTextAnimationControls) {
        const textControls = getTextAnimationControls();
        if (textControls && textControls.animateFade) {
          textControls.animateFade(tl, 0);
        }
      }

      if (leftDoorRef.current && rightDoorRef.current &&
          leftDoorInitialPos.current && rightDoorInitialPos.current) {
        
        const leftOpenOffset = new THREE.Vector3(0, 0, -0.6);
        const rightOpenOffset = new THREE.Vector3(0, 0, 0.6);

        tl.to(leftDoorRef.current.position, {
          z: leftDoorInitialPos.current.z + leftOpenOffset.z,
          duration: 0.8,
          ease: 'power2.out'
        }, 0);

        tl.to(rightDoorRef.current.position, {
          z: rightDoorInitialPos.current.z + rightOpenOffset.z,
          duration: 0.8,
          ease: 'power2.out'
        }, 0);

        if (logoOuterRef.current && logoInnerRef.current &&
            logoOuterInitialPos.current && logoInnerInitialPos.current) {

          tl.to(logoOuterRef.current.position, {
            y: logoOuterInitialPos.current.y + 0.1,
            duration: 0.8,
            ease: 'power2.out'
          }, 0);

          tl.to(logoInnerRef.current.position, {
            y: logoInnerInitialPos.current.y + 0.2,
            duration: 0.8,
            ease: 'power2.out'
          }, 0);

          const matOuter = logoOuterRef.current.material as THREE.MeshStandardMaterial;
          const matInner = logoInnerRef.current.material as THREE.MeshStandardMaterial;

          [matOuter, matInner].forEach(mat => {
            tl.to(mat, {
              opacity: 0,
              duration: 0.8,
              ease: 'power2.out',
              onUpdate: () => {
                if (!mat.transparent) mat.transparent = true;
              }
            }, 0);
          });
        }
      }

      tl.to(camera.position, {
        x: -40, y: 1, z: 20,
        duration: 1,
        ease: 'power2.inOut',
      }, 0);

      tl.to(camera.rotation, {
        x: 0,
        y: -Math.PI / 4,
        z: 0,
        duration: 1,
        ease: 'power2.inOut',
      }, 0);

      tl.to(camera.position, {
        x: 13, y: 0, z: -35,
        duration: 1,
        ease: 'power2.inOut',
      }, '+=0');
    }, 500);
  };

  return (
    <mesh position={[15, -18, -5]}>
      <primitive
        ref={boxRef}
        object={scene}
        scale={8.0}
        onClick={handleZoom}
        onPointerOver={() => { isHovered.current = true; }}
        onPointerOut={() => { isHovered.current = false; }}
        cursor="pointer"
      />
    </mesh>
  );
};

export default Box3D;
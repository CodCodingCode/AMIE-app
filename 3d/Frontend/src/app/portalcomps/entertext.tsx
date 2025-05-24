import React, { useRef, useEffect } from 'react';
import { useGLTF } from '@react-three/drei';
import { Group, Mesh, MeshStandardMaterial } from 'three';
import gsap from 'gsap';

interface EnterTextModelProps {
  startFade?: boolean;
  // Allow any other props to be passed to the primitive
  [key: string]: any; 
}

function EnterTextModel({ startFade, ...props }: EnterTextModelProps) {
  const { scene } = useGLTF('/textagain.glb');
  const modelRef = useRef<Group>(null);
  const materialRefs = useRef<MeshStandardMaterial[]>([]);

  useEffect(() => {
    // Collect materials on mount
    if (modelRef.current) {
      materialRefs.current = [];
      modelRef.current.traverse((child) => {
        if (child instanceof Mesh && child.material instanceof MeshStandardMaterial) {
          const mat = child.material.clone() as MeshStandardMaterial; // Clone to avoid altering cache
          mat.transparent = true;
          mat.opacity = 1;
          child.material = mat; // Assign cloned material
          materialRefs.current.push(mat);
        }
      });
    }
  }, [scene]); // Rerun if scene changes

  useEffect(() => {
    if (startFade && materialRefs.current.length > 0) {
      gsap.to(materialRefs.current.map(m => m), {
        opacity: 0,
        duration: 0.5,
        ease: 'power1.out',
        onComplete: () => {
          // Optionally hide the model after fade
          if (modelRef.current) {
            modelRef.current.visible = false;
          }
        }
      });
    }
  }, [startFade]);

  return <primitive ref={modelRef} object={scene} {...props} />;
}

interface EnterTextProps {
  startFade?: boolean;
  position?: [number, number, number];
  rotation?: [number, number, number];
  scale?: number;
}

export default function EnterText({ 
  startFade,
  position,
  rotation,
  scale 
}: EnterTextProps) {
  return (
    <>
      <EnterTextModel 
        startFade={startFade} 
        position={position} 
        rotation={rotation} 
        scale={scale}
      />
    </>
  );
} 
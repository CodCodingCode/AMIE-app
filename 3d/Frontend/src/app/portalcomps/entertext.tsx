import React, { useRef, useEffect, useImperativeHandle, forwardRef } from 'react';
import { useGLTF } from '@react-three/drei';
import { Group, Mesh, MeshStandardMaterial } from 'three';
import gsap from 'gsap';

// Define the type for the imperative methods exposed by EnterTextModel
export interface EnterTextModelHandles {
  animateFade: (timeline: gsap.core.Timeline, startTimeLabel: string) => void;
}

interface EnterTextModelProps {
  // Allow any other props to be passed to the primitive
  [key: string]: any;
}

const EnterTextModel = forwardRef<EnterTextModelHandles, EnterTextModelProps>(({ ...props }, ref) => {
  const { scene } = useGLTF('/textagain.glb');
  const modelRef = useRef<Group>(null);
  const materialRefs = useRef<MeshStandardMaterial[]>([]);

  useEffect(() => {
    if (modelRef.current) {
      materialRefs.current = [];
      modelRef.current.traverse((child) => {
        if (child instanceof Mesh && child.material instanceof MeshStandardMaterial) {
          const mat = child.material.clone() as MeshStandardMaterial;
          mat.transparent = true;
          mat.opacity = 1;
          child.material = mat;
          materialRefs.current.push(mat);
        }
      });
    }
  }, [scene]);

  useImperativeHandle(ref, () => ({
    animateFade: (timeline, startTimeLabel) => {
      if (materialRefs.current.length > 0) {
        timeline.to(materialRefs.current.map(m => m), {
          opacity: 0,
          duration: 0.5,
          ease: 'power1.out',
          onComplete: () => {
            if (modelRef.current) {
              modelRef.current.visible = false;
            }
          }
        }, startTimeLabel);
      }
    }
  }));

  return <primitive ref={modelRef} object={scene} {...props} />;
});
EnterTextModel.displayName = 'EnterTextModel';

// Define the type for the imperative methods exposed by EnterText (if it needs to expose any itself, or re-expose from EnterTextModel)
export interface EnterTextHandles extends EnterTextModelHandles {}

interface EnterTextProps {
  position?: [number, number, number];
  rotation?: [number, number, number];
  scale?: number;
}

const EnterText = forwardRef<EnterTextHandles, EnterTextProps>(({ 
  position,
  rotation,
  scale 
}, ref) => {
  // If EnterTextModel is the one with GLTF and animation, we need a ref to it.
  const modelComponentRef = useRef<EnterTextModelHandles>(null);

  // Re-expose animateFade from EnterTextModel
  useImperativeHandle(ref, () => ({
    animateFade: (timeline, startTimeLabel) => {
      modelComponentRef.current?.animateFade(timeline, startTimeLabel);
    }
  }));

  return (
    <>
      <EnterTextModel 
        ref={modelComponentRef}
        position={position} 
        rotation={rotation} 
        scale={scale}
      />
    </>
  );
});
EnterText.displayName = 'EnterText';

export default EnterText; 
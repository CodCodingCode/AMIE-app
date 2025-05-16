import React, { useState, useEffect } from 'react';
import { useThree, useFrame } from '@react-three/fiber';
import * as THREE from 'three';

type MouseParallaxProps = {
  strength?: number;
  isEnabled?: boolean;
  targetCamera?: THREE.PerspectiveCamera | THREE.OrthographicCamera;
  shouldLookAtCenter?: boolean;
  dampingFactor?: number;
};

type MousePosition = [number, number];

/**
 * MouseParallax component for camera movement based on mouse position
 * Creates a subtle parallax effect for 3D scenes
 */
const MouseParallax: React.FC<MouseParallaxProps> = ({
  strength = 0.5,
  isEnabled = true,
  shouldLookAtCenter = true,
  dampingFactor = 0.10,
}) => {
  const { camera } = useThree();
  const [mousePos, setMousePos] = useState<MousePosition>([0, 0]);
  const [initialCameraPosition] = useState(() => camera.position.clone());

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

  // Apply parallax effect
  useFrame(() => {
    if (!isEnabled) return;
  
    // Calculate target position based on mouse movement and initial camera position
    const targetX = initialCameraPosition.x - mousePos[0] * strength;
    const targetY = initialCameraPosition.y + mousePos[1] * strength;

    // Apply smooth damping to camera movement
    camera.position.x += (targetX - camera.position.x) * dampingFactor;
    camera.position.y += (targetY - camera.position.y) * dampingFactor;
    
    // Optionally make camera look at the center
    if (shouldLookAtCenter) {
      camera.lookAt(0, 0, 0);
    }
  });

  // This component doesn't render anything directly
  return null;
};

export default MouseParallax; 
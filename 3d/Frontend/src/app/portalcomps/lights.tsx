import React from 'react';
import * as THREE from 'three';

// Scene lighting
const BasicLights = () => (
  <>
    <ambientLight intensity={0.4} color="#b9d5ff" />
    <directionalLight 
      position={[5, 8, 5]} 
      intensity={1.2} 
      color="#ffffff" 
    />
    <directionalLight position={[-5, 3, 0]} intensity={0.5} color="#4d71ff" />
    
    {/* Optional: Helper to visualize the shadow camera (uncomment for debugging) */}
    {/* <cameraHelper args={[new THREE.DirectionalLight().shadow.camera]} /> */}
  </>
);

export default BasicLights;
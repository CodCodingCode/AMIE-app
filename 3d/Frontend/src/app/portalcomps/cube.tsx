import React from 'react';
import * as THREE from 'three';

type SimplePlatformProps = {
  position: [number, number, number];
  rotation?: number;
  width?: number;
  height?: number;
  length?: number;
  color?: string;
};

const Platform = ({
  position,
  rotation,
  width,
  height,
  length,
  color
}: SimplePlatformProps) => {
  return (
    <mesh position={position} rotation={[0, rotation || 0, 0]} castShadow receiveShadow>
      <boxGeometry args={[width, height, length]} />
      <meshStandardMaterial color={color} />
    </mesh>
  );
};

export default Platform;
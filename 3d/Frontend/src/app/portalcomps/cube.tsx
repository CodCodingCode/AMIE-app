import React from 'react';
import * as THREE from 'three';

type SimplePlatformProps = {
  position: [number, number, number];
  rotation?: number;
  width?: number;
  height?: number;
  length?: number;
  color?: string;
  opacity?: number;
};

const Platform = ({
  position,
  rotation,
  width = 1,
  height = 1,
  length = 1,
  color = '#ffffff',
  opacity = 1
}: SimplePlatformProps) => {
  return (
    <mesh position={position} rotation={[0, rotation || 0, 0]} castShadow receiveShadow>
      <boxGeometry args={[width, height, length]} />
      <meshStandardMaterial
        color={color}
        transparent={opacity < 1}
        opacity={opacity}
        polygonOffset
        polygonOffsetFactor={-1}
        polygonOffsetUnits={-1}
      />
    </mesh>
  );
};

export default Platform;

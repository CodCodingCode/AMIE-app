import React, { useRef, useEffect, createRef } from 'react';
import { useFrame, useThree } from '@react-three/fiber';
import { RigidBody, RapierRigidBody } from '@react-three/rapier';
import * as THREE from 'three';
import { ConvexGeometry } from 'three/examples/jsm/geometries/ConvexGeometry.js';

// Rock data structure
type Rock = {
  ref: React.RefObject<RapierRigidBody | null>;
  position: THREE.Vector3;
  velocity: THREE.Vector3;
  geometry: ConvexGeometry;
  scale: number;
};

// SpaceRocks component
const SpaceRocks = () => {
  const rockMap = useRef<Map<string, Rock>>(new Map());
  const rockMaterial = useRef<THREE.MeshStandardMaterial>(
    new THREE.MeshStandardMaterial({
      color: '#444444',
      roughness: 0.7,
      metalness: 0.1,
    })
  );
  const { camera } = useThree();

  // Generate random rock geometry
  const generateRockGeometry = () => {
    const vertices: THREE.Vector3[] = [];
    for (let i = 0; i < 50; i++) {
      vertices.push(new THREE.Vector3(
        (Math.random() - 0.5) * 3,
        (Math.random() - 0.5) * 3,
        (Math.random() - 0.5) * 3
      ));
    }
    const geometry = new ConvexGeometry(vertices);
    return geometry;
  };

  // Keep rocks within screen bounds
  const keepRocksInBounds = () => {
    // Calculate view frustum boundaries at different depths
    const perspCamera = camera as THREE.PerspectiveCamera;
    const frustumHeight = (perspCamera.position.z - 20) * Math.tan(THREE.MathUtils.degToRad(perspCamera.fov / 2)) * 2;
    const frustumWidth = frustumHeight * perspCamera.aspect;
    
    const bounds = {
      left: -frustumWidth / 2,
      right: frustumWidth / 2,
      top: frustumHeight / 2,
      bottom: -frustumHeight / 2,
      near: camera.position.z - 20,
      far: camera.position.z + 20
    };
    
    rockMap.current.forEach((rock) => {
      const rigidBody = rock.ref.current;
      if (!rigidBody) return;
      
      const position = rigidBody.translation();
      const velocity = rigidBody.linvel();
      let needsUpdate = false;
      
      // Check X boundaries
      if (position.x < bounds.left) {
        position.x = bounds.left;
        velocity.x = Math.abs(velocity.x) * 0.5; // Bounce with reduced velocity
        needsUpdate = true;
      } else if (position.x > bounds.right) {
        position.x = bounds.right;
        velocity.x = -Math.abs(velocity.x) * 0.5;
        needsUpdate = true;
      }
      
      // Check Y boundaries
      if (position.y < bounds.bottom) {
        position.y = bounds.bottom;
        velocity.y = Math.abs(velocity.y) * 0.5;
        needsUpdate = true;
      } else if (position.y > bounds.top) {
        position.y = bounds.top;
        velocity.y = -Math.abs(velocity.y) * 0.5;
        needsUpdate = true;
      }
      
      // Check Z boundaries
      if (position.z < bounds.near) {
        position.z = bounds.near;
        velocity.z = Math.abs(velocity.z) * 0.5;
        needsUpdate = true;
      } else if (position.z > bounds.far) {
        position.z = bounds.far;
        velocity.z = -Math.abs(velocity.z) * 0.5;
        needsUpdate = true;
      }
      
      // Update position and velocity if needed
      if (needsUpdate) {
        rigidBody.setTranslation(position, true);
        rigidBody.setLinvel(velocity, true);
      }
    });
  };
  
  // Use frame to check and update rock positions
  useFrame(() => {
    keepRocksInBounds();
  });

  // Initialize rocks
  useEffect(() => {
    const idPrefix = Math.random().toString(36).substr(2, 9);
    
    // Create rocks around the origin (0,0,0)
    for (let i = 0; i < 10; i++) {
      const rockId = `${idPrefix}_rock_${i + 1}`;
      
      // Position close to origin with slight offset to prevent overlap
      const position = new THREE.Vector3(
        (Math.random() - 0.5) * 10,
        (Math.random() - 0.5) * 10,
        (Math.random() - 0.5) * 10
      );
      
      rockMap.current.set(rockId, {
        ref: createRef<RapierRigidBody | null>(),
        position: position,
        velocity: new THREE.Vector3(
          (Math.random() - 0.5) * 3, // Reduced velocity
          (Math.random() - 0.5) * 3,
          (Math.random() - 0.5) * 3
        ),
        geometry: generateRockGeometry(),
        scale: 0.5 + Math.random() * 1, // Smaller rocks
      });
    }
  }, []);

  return (
    <>
      {Array.from(rockMap.current.entries()).map(([key, rock]) => (
        <RigidBody
          key={key}
          ref={rock.ref}
          position={[rock.position.x, rock.position.y, rock.position.z]}
          linearVelocity={[rock.velocity.x, rock.velocity.y, rock.velocity.z]}
          angularVelocity={[
            (Math.random() - 0.5) * 1,
            (Math.random() - 0.5) * 1,
            (Math.random() - 0.5) * 1
          ]}
          restitution={0.9}
          friction={0.1}
        >
          <mesh geometry={rock.geometry} scale={rock.scale}>
            <primitive attach="material" object={rockMaterial.current} />
          </mesh>
        </RigidBody>
      ))}
    </>
  );
};

export default SpaceRocks;
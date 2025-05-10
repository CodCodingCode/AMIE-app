'use client'

import React, { useRef, useState, Suspense, useEffect } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { Environment, Stars, PerspectiveCamera } from '@react-three/drei'
import { Mesh, Vector3 } from 'three'
import { motion } from 'framer-motion'
import { useRouter } from 'next/navigation'

// The main scene component that contains everything
const PortalScene = () => {
  const [isZooming, setIsZooming] = useState(false)
  const router = useRouter()
  const portalPosition: [number, number, number] = [0, 0, 0]
  
  const handlePortalEnter = () => {
    setIsZooming(true)
  }
  
  const handleZoomComplete = () => {
    // Navigate to loading screen when zoom completes
    router.push('/loading')
  }
  
  return (
    <div className="h-screen w-full">
      <Canvas>
        <PerspectiveCamera makeDefault position={[0, 0, 5]} fov={75} />
        <ambientLight intensity={0.5} />
        <pointLight position={[10, 10, 10]} intensity={1} />
        <pointLight position={[-10, -10, -10]} color="#4CC9F0" intensity={0.5} />
        
        <Suspense fallback={null}>
          <Environment preset="sunset" />
          <Stars radius={100} depth={50} count={5000} factor={4} fade />
          
          {/* Camera controller */}
          <PortalCameraController 
            isZooming={isZooming}
            portalPosition={portalPosition}
            onZoomComplete={handleZoomComplete}
          />
          
          {/* Main portal object */}
          <Portal 
            position={portalPosition} 
            color="#8352FD" 
            onPortalEnter={handlePortalEnter}
          />
        </Suspense>
      </Canvas>
    </div>
  )
}

// The portal component that handles the visual appearance and interaction
const Portal = ({ 
  position = [0, 0, 0], 
  color = "#8352FD", 
  onPortalEnter 
}: {
  position?: [number, number, number];
  color?: string;
  onPortalEnter: () => void;
}) => {
  const meshRef = useRef<Mesh>(null!)
  const [hovered, setHovered] = useState(false)
  const [clicked, setClicked] = useState(false)
  const [scale, setScale] = useState(1)
  
  // Handle portal click
  const handlePortalClick = () => {
    if (!clicked) {
      setClicked(true)
      // Notify parent component that portal was clicked
      setTimeout(() => {
        onPortalEnter()
      }, 500)
    }
  }

  // Handle hover effect
  useEffect(() => {
    setScale(hovered && !clicked ? 1.1 : 1)
  }, [hovered, clicked])

  // Animate portal
  useFrame((state, delta) => {
    if (meshRef.current) {
      if (!clicked) {
        // Gentle rotation when not clicked
        meshRef.current.rotation.y += delta * 0.2
        meshRef.current.rotation.z += delta * 0.1
      } else {
        // Spin faster when clicked
        meshRef.current.rotation.y += delta * 2
        meshRef.current.rotation.z += delta
        
        // Scale up when clicked
        meshRef.current.scale.multiplyScalar(1 + delta)
      }
    }
  })

  return (
    <mesh
      ref={meshRef}
      position={position as any}
      scale={[scale, scale, scale]}
      onClick={handlePortalClick}
      onPointerOver={() => setHovered(true)}
      onPointerOut={() => setHovered(false)}
    >
      <torusGeometry args={[1, 0.3, 16, 100]} />
      <meshStandardMaterial 
        color={color} 
        emissive={color} 
        emissiveIntensity={hovered ? 2 : 1}
        toneMapped={false}
      />
      {/* Inner portal glow */}
      <mesh position={[0, 0, 0]}>
        <planeGeometry args={[1.5, 1.5]} />
        <meshBasicMaterial 
          color={color} 
          transparent={true} 
          opacity={0.5}
        />
      </mesh>
    </mesh>
  )
}

// Camera controller component for creating the portal zoom effect
const PortalCameraController = ({ 
  isZooming, 
  portalPosition, 
  onZoomComplete 
}: {
  isZooming: boolean;
  portalPosition: [number, number, number];
  onZoomComplete: () => void;
}) => {
  const [zoomProgress, setZoomProgress] = useState(0)
  const portalPos = new Vector3(...portalPosition)
  
  useFrame((state, delta) => {
    if (isZooming) {
      // Update zoom progress
      setZoomProgress((prev) => {
        const newProgress = Math.min(prev + delta * 0.7, 1)
        if (newProgress >= 1 && prev < 1) {
          onZoomComplete()
        }
        return newProgress
      })
      
      // Get current camera position
      const cameraPos = state.camera.position
      
      // Calculate the direction vector from camera to portal
      const direction = new Vector3()
      direction.subVectors(portalPos, cameraPos).normalize()
      
      // Move camera closer to portal with accelerating speed
      const easeProgress = Math.pow(zoomProgress, 3) // Cubic easing
      const moveDistance = 10 * delta * (1 + easeProgress * 30)
      
      cameraPos.addScaledVector(direction, moveDistance)
      
      // Point camera to look at portal
      state.camera.lookAt(portalPos)
      
      // Add some camera shake for dramatic effect
      if (zoomProgress > 0.5) {
        const intensity = (zoomProgress - 0.5) * 0.05
        state.camera.position.x += (Math.random() - 0.5) * intensity
        state.camera.position.y += (Math.random() - 0.5) * intensity
      }
    }
  })
  
  return null
}

export default PortalScene
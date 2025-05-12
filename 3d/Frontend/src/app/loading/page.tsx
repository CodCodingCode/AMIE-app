'use client'

import React, { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Canvas } from '@react-three/fiber'
import { PerspectiveCamera, Preload } from '@react-three/drei'

// Basic lighting component for the scene
const BasicLights = () => {
  return (
    <>
      <ambientLight intensity={0.4} color="#b9d5ff" />
      <directionalLight
        position={[5, 8, 5]}
        intensity={1.2}
        color="#ffffff"
        castShadow
      />
      <directionalLight 
        position={[-5, 3, 0]} 
        intensity={0.5} 
        color="#4d71ff"
      />
    </>
  );
};

// Loading screen page
export default function LoadingPage() {
  const [progress, setProgress] = useState(0)
  const router = useRouter()
  
  useEffect(() => {
    // Animate progress from 0 to 100 over 3 seconds
    const duration = 3000
    const startTime = Date.now()
    const endTime = startTime + duration
    
    const updateProgress = () => {
      const currentTime = Date.now()
      const elapsed = currentTime - startTime
      const newProgress = Math.min((elapsed / duration) * 100, 100)
      
      setProgress(newProgress)
      
      if (currentTime < endTime) {
        requestAnimationFrame(updateProgress)
      } else {
        // Navigate to chat when loading is complete
        setTimeout(() => {
          router.push('/chat')
        }, 200)
      }
    }
    
    const animationId = requestAnimationFrame(updateProgress)
    
    // Cleanup animation frame on unmount
    return () => {
      cancelAnimationFrame(animationId)
    }
  }, [router])
  
  return (
    <div className="h-screen w-full bg-black">
      <Canvas shadows>
        <PerspectiveCamera makeDefault position={[0, 0, 10]} fov={75} />
        <fog attach="fog" args={['#070b34', 10, 50]} />
        <BasicLights />
        <Preload all />
      </Canvas>
      
      {/* Overlay the 2D loading UI */}
      <div className="fixed inset-0 bg-black bg-opacity-70 flex flex-col items-center justify-center z-50 pointer-events-none">
        {/* Portal animation using SVG */}
        <svg width="200" height="200" viewBox="0 0 100 100">
          <circle
            cx="50"
            cy="50"
            r="30"
            fill="none"
            stroke="#8352FD"
            strokeWidth="2"
            strokeDasharray="188.5"
            strokeDashoffset={188.5 - (188.5 * progress / 100)}
            transform="rotate(-90 50 50)"
          />
          <circle
            cx="50"
            cy="50"
            r="20"
            fill="none"
            stroke="#4CC9F0"
            strokeWidth="3"
            strokeDasharray="125.7"
            strokeDashoffset={125.7 - (125.7 * progress / 100)}
            transform="rotate(90 50 50)"
          />
          <circle
            cx="50"
            cy="50"
            r="10"
            fill="#8352FD"
            opacity={progress / 100}
          />
        </svg>
        
        <div className="mt-8 w-64">
          <div className="relative h-2 bg-gray-800 rounded-full overflow-hidden">
            <div 
              className="absolute top-0 left-0 h-full bg-gradient-to-r from-purple-500 to-blue-500"
              style={{ width: `${progress}%` }}
            />
          </div>
          <p className="text-white mt-2 text-center font-mono">
            {Math.round(progress)}%
          </p>
        </div>
        
        <div className="text-white mt-8 text-lg text-center">
          <p className="animate-pulse">Traveling through dimensions...</p>
          <p className="text-sm text-gray-400 mt-2">Please wait while we prepare your destination</p>
        </div>
      </div>
    </div>
  )
}
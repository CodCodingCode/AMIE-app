import React from 'react'
import { Canvas } from '@react-three/fiber'
import { OrbitControls, useGLTF } from '@react-three/drei'

function EnterTextModel(props: any) {
  const gltf = useGLTF('/entertext.glb')
  return <primitive object={gltf.scene} {...props} />
}

export default function EnterText() {
  return (
    <>
      <EnterTextModel scale={1} position={[-5, 2, 0]} />
    </>
  )
}

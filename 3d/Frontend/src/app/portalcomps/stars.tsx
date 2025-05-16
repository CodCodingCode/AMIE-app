import { Stars } from "@react-three/drei";
import { useFrame } from "@react-three/fiber";
import { useRef } from "react";
import { Group } from "three";

// Background stars with subtle animation
const AnimatedStars = () => {
    const starsRef = useRef<Group>(null);
    useFrame(() => starsRef.current && (starsRef.current.rotation.y += 0.0005));
    
    return (
      <group ref={starsRef}>
        <Stars radius={40} depth={20} count={1000} factor={2} saturation={0.5} fade speed={0.3} />
      </group>
    );
  };

export default AnimatedStars;
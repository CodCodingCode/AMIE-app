// components/buttons.tsx
import { useState } from 'react';

export function Button({ onClick, children }: { onClick?: () => void; children: React.ReactNode }) {
  const [isHovered, setIsHovered] = useState(false);
  
  return (
    <div 
      className="relative inline-block cursor-pointer"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onClick={onClick}
    >
      {/* Glow effect - adjusted opacity and blur for subtler effect */}
      <div className="absolute -inset-1 rounded-full bg-pink-300 opacity-50 blur-md"></div>
      
      {/* Main button */}
      <button className="relative px-12 py-4 rounded-full bg-[#2a1708] text-white font-bold text-2xl overflow-hidden">
        {/* Brown oval background element */}
        <div 
          className="absolute w-32 h-32 rounded-full bg-[#593520] left-1/2 -translate-x-1/2 transition-all duration-300"
          style={{ 
            bottom: isHovered ? '-60px' : '-100px',
            opacity: 0.9
          }}
        ></div>
        
        {/* Button text */}
        <span className="relative z-10">{children}</span>
      </button>
    </div>
  );
}
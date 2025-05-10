"use client";
import { useEffect, useState } from 'react';

export default function SplineBackground() {
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    // Dynamically load the Spline viewer script only once
    if (!document.querySelector('script[data-spline-viewer]')) {
      const script = document.createElement('script');
      script.type = 'module';
      script.src = 'https://unpkg.com/@splinetool/viewer@1.9.92/build/spline-viewer.js';
      script.setAttribute('data-spline-viewer', 'true');
      script.onload = () => {
        setIsReady(true);
        console.log('Spline viewer script loaded');
      };
      document.body.appendChild(script);
    } else {
      setIsReady(true);
    }
    // Check if custom element is defined
    setTimeout(() => {
      if (window.customElements && customElements.get('spline-viewer')) {
        console.log('spline-viewer custom element is defined');
      } else {
        console.warn('spline-viewer custom element is NOT defined');
      }
    }, 2000);
  }, []);

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      width: '100vw',
      height: '100vh',
      zIndex: 1, // DEBUG: bring to front
      pointerEvents: 'auto', // DEBUG: allow interaction
      overflow: 'hidden',
    }}>
      {/* Spline viewer as background */}
      <spline-viewer
        url="https://prod.spline.design/hHNAefCbGOXdNtaU/scene.splinecode"
        style={{
          width: '100vw',
          height: '100vh',
          display: 'block',
        }}
      ></spline-viewer>
    </div>
  );
} 
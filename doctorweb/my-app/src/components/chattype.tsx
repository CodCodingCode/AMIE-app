'use client';
import { useState, useEffect } from 'react';

interface TypewriterEffectProps {
  text: string;
  delay?: number;
  onComplete?: () => void;
}

export const TypewriterEffect = ({ text, delay = 50, onComplete }: TypewriterEffectProps) => {
  const [displayedText, setDisplayedText] = useState('');
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isComplete, setIsComplete] = useState(false);

  useEffect(() => {
    if (currentIndex < text.length) {
      const timeout = setTimeout(() => {
        setDisplayedText(prev => prev + text[currentIndex]);
        setCurrentIndex(prev => prev + 1);
      }, delay);
      
      return () => clearTimeout(timeout);
    } else if (!isComplete) {
      setIsComplete(true);
      onComplete?.();
    }
  }, [currentIndex, delay, text, isComplete, onComplete]);

  return (
    <span className="typewriter-text">
      {displayedText}
      <span className="cursor-blink">|</span>
      <style jsx>{`
        .typewriter-text {
          display: inline-block;
          position: relative;
        }
        .cursor-blink {
          display: ${isComplete ? 'none' : 'inline-block'};
          opacity: 1;
          margin-left: 2px;
          animation: blink 1s infinite;
        }
        @keyframes blink {
          0%, 100% { opacity: 1; }
          50% { opacity: 0; }
        }
      `}</style>
    </span>
  );
};
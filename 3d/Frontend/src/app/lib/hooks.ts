import { useState, useEffect, useCallback } from 'react';
import { scrollToTop, dispatchCustomEvent } from './utils';

// Hook for scroll-based effects
export const useScrollEffect = (threshold: number = 50) => {
  const [isScrolled, setIsScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > threshold);
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, [threshold]);

  return isScrolled;
};

// Hook for mobile menu state
export const useMobileMenu = () => {
  const [isOpen, setIsOpen] = useState(false);

  const toggle = useCallback(() => setIsOpen((prev: boolean) => !prev), []);
  const close = useCallback(() => setIsOpen(false), []);

  return { isOpen, toggle, close };
};

// Hook for managing bluebox animation state
export const useBlueboxAnimation = () => {
  const [isAnimationStarted, setIsAnimationStarted] = useState(false);

  const handleGetStartedClick = useCallback(() => {
    // Check if we're already at the top
    if (window.scrollY <= 10) {
      // Already at top, trigger immediately
      dispatchCustomEvent('triggerBlueboxAnimation');
      return;
    }

    // Scroll to top with faster, smoother behavior
    window.scrollTo({ 
      top: 0, 
      behavior: 'smooth' 
    });

    // Use requestAnimationFrame for better performance
    const checkScroll = () => {
      if (window.scrollY <= 10) {
        // We've reached the top, trigger animation immediately
        dispatchCustomEvent('triggerBlueboxAnimation');
      } else {
        // Continue checking on next frame
        requestAnimationFrame(checkScroll);
      }
    };

    // Start checking on next frame
    requestAnimationFrame(checkScroll);

    // Fallback timeout (shorter and more reliable)
    setTimeout(() => {
      if (window.scrollY <= 50) { // More lenient fallback
        dispatchCustomEvent('triggerBlueboxAnimation');
      }
    }, 1000); // Reduced to 1 second
  }, []);

  const resetAnimationTrigger = useCallback(() => {
    setIsAnimationStarted(false);
  }, []);

  useEffect(() => {
    const handleBlueboxAnimation = () => {
      setIsAnimationStarted(true);
    };

    window.addEventListener('triggerBlueboxAnimation', handleBlueboxAnimation);
    return () => window.removeEventListener('triggerBlueboxAnimation', handleBlueboxAnimation);
  }, []);

  return { isAnimationStarted, handleGetStartedClick, resetAnimationTrigger };
};

// Hook for global window functions
export const useGlobalFunctions = (functions: Record<string, Function>) => {
  useEffect(() => {
    if (typeof window !== 'undefined') {
      Object.entries(functions).forEach(([name, fn]) => {
        (window as any)[name] = fn;
      });
    }
    
    return () => {
      if (typeof window !== 'undefined') {
        Object.keys(functions).forEach(name => {
          delete (window as any)[name];
        });
      }
    };
  }, [functions]);
};
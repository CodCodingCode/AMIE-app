// animations/fadeIn.js
export const fadeInUp = {
    initial: { opacity: 0, y: 20 },
    whileInView: { opacity: 1, y: 0 },
    transition: { duration: 0.5 },
    viewport: {
      once: true,      // triggers only the first time it enters the viewport
      amount: 0.5      // only trigger when 50% of the component is visible
    },
  };
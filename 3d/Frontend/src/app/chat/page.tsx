'use client';

import React, { useEffect } from 'react';
import { Sidebar, SidebarMenu } from './sidebar';
import ChatWindow from './chatwindow';
import { motion } from 'framer-motion';

// Simple page that shows the chat interface for all users
export default function ChatPage() {
  // Force create a new chat whenever the chat page is loaded directly (not from another chat)
  useEffect(() => {
    // Only create a new chat if we're coming from outside the app
    // and not from another chat
    if (typeof window !== 'undefined' && window.createNewChat) {
      // Check if we're navigating directly to the chat page
      // without coming from another chat
      const referrer = document.referrer;
      const isDirectNavigation = !referrer || !referrer.includes('/chat');
      
      if (isDirectNavigation) {
        // Short delay to ensure the chat window is fully loaded
        const timer = setTimeout(() => {
          window.createNewChat?.();
        }, 100);
        
        return () => clearTimeout(timer);
      }
    }
  }, []);

  // Animation variants for fade-in
  const pageAnimationVariants = {
    hidden: { opacity: 0 },
    visible: { 
      opacity: 1,
      transition: {
        duration: 0.6,
        ease: "easeInOut",
        when: "beforeChildren",
        staggerChildren: 0.2
      }
    }
  };

  const childAnimationVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { 
      opacity: 1, 
      y: 0,
      transition: {
        duration: 0.4,
        ease: "easeOut"
      }
    }
  };

  return (
    <motion.div 
      className="flex h-screen bg-gray-100 dark:bg-neutral-900"
      initial="hidden"
      animate="visible"
      variants={pageAnimationVariants}
    >
      {/* Sidebar with absolute positioning to prevent affecting main content */}
      <motion.div 
        className="absolute h-full z-10"
        variants={childAnimationVariants}
      >
        <Sidebar>
          <SidebarMenu />
        </Sidebar>
      </motion.div>
      
      {/* Main content with fixed position and width */}
      <motion.div 
        className="flex-1 h-full overflow-hidden ml-[80px] md:ml-[80px]"
        variants={childAnimationVariants}
      >
        <ChatWindow />
      </motion.div>
    </motion.div>
  );
}

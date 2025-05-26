'use client';

import React, { useEffect } from 'react';
import { Sidebar, SidebarMenu } from './sidebar';
import ChatWindow from './chatwindow';
import { motion } from 'framer-motion';

// Simple page that shows the chat interface for all users
export default function ChatPage() {
  // Removed auto-creation of new chat on page load - only create when user clicks "New Chat"

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
      className="relative h-screen bg-neutral-900 overflow-hidden"
      initial="hidden"
      animate="visible"
      variants={pageAnimationVariants}
    >
      {/* Main content takes full width */}
      <motion.div 
        className="w-full h-full"
        variants={childAnimationVariants}
      >
        <ChatWindow />
      </motion.div>
      
      {/* Sidebar overlays on top with fixed positioning */}
      <motion.div 
        className="fixed top-0 left-0 h-full z-50"
        variants={childAnimationVariants}
      >
        <Sidebar>
          <SidebarMenu />
        </Sidebar>
      </motion.div>
    </motion.div>
  );
}
'use client';

import React from 'react';
import { Sidebar, SidebarMenu } from './sidebar';
import ChatWindow from './chatwindow';
import { motion } from 'framer-motion';

export default function ChatPage() {
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
    <div className="flex h-screen bg-white">
      <motion.div 
        className="absolute h-full z-20"
        initial="hidden"
        animate="visible"
        variants={childAnimationVariants}
      >
        <Sidebar>
          <SidebarMenu />
        </Sidebar>
      </motion.div>
      
      <motion.div 
        className="flex-1 h-full overflow-hidden ml-[80px] md:ml-[80px]"
        initial="hidden"
        animate="visible"
        variants={childAnimationVariants}
      >
        <ChatWindow />
      </motion.div>
    </div>
  );
}

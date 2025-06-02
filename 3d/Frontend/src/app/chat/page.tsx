'use client';

import React, { useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { Sidebar, SidebarMenu } from './sidebar';
import ChatWindow from './chatwindow';

// Simple page that shows the chat interface for all users
export default function ChatPage() {
  const searchParams = useSearchParams();
  const chatId = searchParams.get('id');
  const [isInitialized, setIsInitialized] = useState(false);

  // Load specific chat when URL contains chat ID
  useEffect(() => {
    // Mark as initialized immediately to prevent flickering
    setIsInitialized(true);
    
    if (chatId && typeof window !== 'undefined' && window.loadChat) {
      // Minimal delay only for ensuring DOM is ready
      const timer = setTimeout(() => {
        window.loadChat?.(chatId);
      }, 50);
      return () => clearTimeout(timer);
    }
  }, [chatId]);

  // Simple fade-in without complex staggering
  return (
    <div 
      className={`relative h-screen bg-neutral-900 overflow-hidden transition-opacity duration-300 ${
        isInitialized ? 'opacity-100' : 'opacity-0'
      }`}
    >
      {/* Main content takes full width */}
      <div className="w-full h-full">
        <ChatWindow />
      </div>
      
      {/* Sidebar overlays on top with fixed positioning */}
      <div className="fixed top-0 left-0 h-full z-50">
        <Sidebar>
          <SidebarMenu />
        </Sidebar>
      </div>
    </div>
  );
}
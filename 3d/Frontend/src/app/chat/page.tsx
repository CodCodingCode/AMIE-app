'use client';

import React, { useEffect, useState, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { Sidebar, SidebarMenu } from './sidebar';
import ChatWindow from './chatwindow';
import { ModalProvider } from './ModalContext'; // Import the modal provider

// Inner component containing the original logic
function ChatPageContent() {
  const searchParams = useSearchParams();
  const chatId = searchParams.get('id');
  const [isInitialized, setIsInitialized] = useState(false);

  // Load specific chat when URL contains chat ID
  useEffect(() => {
    // Mark as initialized immediately to prevent flickering
    setIsInitialized(true);
    
    if (chatId && typeof window !== 'undefined' && (window as any).loadChat) {
      // Minimal delay only for ensuring DOM is ready
      const timer = setTimeout(() => {
        (window as any).loadChat?.(chatId);
      }, 50);
      return () => clearTimeout(timer);
    }
  }, [chatId]);

  // Simple fade-in without complex staggering
  return (
    <ModalProvider>
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
    </ModalProvider>
  );
}

// Default export wrapper component with Suspense
export default function ChatPage() {
  return (
    <Suspense fallback={
      <div className="h-screen bg-neutral-900 flex items-center justify-center">
        <p className="text-white text-lg">Loading chat...</p> 
        {/* You can add a spinner here if you have one */}
      </div>
    }>
      <ChatPageContent />
    </Suspense>
  );
}
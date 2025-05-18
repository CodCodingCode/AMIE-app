'use client';

import React from 'react';
import { Sidebar, SidebarMenu } from './sidebar';
import ChatWindow from './chatwindow';

// Simple page that shows the chat interface for all users
export default function ChatPage() {
  return (
    <div className="flex h-screen bg-gray-100 dark:bg-neutral-900">
      <Sidebar>
        <SidebarMenu />
      </Sidebar>
      <div className="flex-1 transition-all duration-300 h-full overflow-hidden">
        <ChatWindow />
      </div>
    </div>
  );
}


'use client';

import React from 'react';
import { Sidebar, SidebarMenu } from './sidebar';
import ChatWindow from './chatwindow';

export default function Chat() {
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
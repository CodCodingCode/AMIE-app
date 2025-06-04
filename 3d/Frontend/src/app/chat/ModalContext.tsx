'use client';

import React, { createContext, useContext, useState } from 'react';
import { createPortal } from 'react-dom';
import SettingsModal from './settings';

interface ModalContextType {
  openSettings: () => void;
  closeSettings: () => void;
  isSettingsOpen: boolean;
}

const ModalContext = createContext<ModalContextType | undefined>(undefined);

export const useModal = () => {
  const context = useContext(ModalContext);
  if (!context) {
    throw new Error('useModal must be used within ModalProvider');
  }
  return context;
};

export const ModalProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);

  const openSettings = () => setIsSettingsOpen(true);
  const closeSettings = () => setIsSettingsOpen(false);

  return (
    <ModalContext.Provider value={{ openSettings, closeSettings, isSettingsOpen }}>
      {children}
      {/* Render modals using portal to document.body */}
      {typeof window !== 'undefined' && createPortal(
        <SettingsModal 
          isOpen={isSettingsOpen} 
          onClose={closeSettings} 
        />,
        document.body
      )}
    </ModalContext.Provider>
  );
};
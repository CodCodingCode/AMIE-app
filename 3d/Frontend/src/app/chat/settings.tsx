'use client';

import React from 'react';
import { useAuth } from '../chat/Auth';
import { IconLogout, IconX, IconSettings } from '@tabler/icons-react';
import { motion, AnimatePresence } from 'framer-motion';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const SettingsModal: React.FC<SettingsModalProps> = ({ isOpen, onClose }) => {
  const { user, logOut } = useAuth();

  const handleSignOut = async () => {
    await logOut();
    onClose(); // Close modal after sign out
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 bg-smokyBlack bg-opacity-90 flex items-center justify-center p-6 z-50"
          onClick={onClose}
        >
          <motion.div
            initial={{ scale: 0.9, opacity: 0, y: 20 }}
            animate={{ scale: 1, opacity: 1, y: 0 }}
            exit={{ scale: 0.9, opacity: 0, y: 20 }}
            transition={{ type: 'spring', stiffness: 300, damping: 30 }}
            onClick={(e) => e.stopPropagation()}
            className="bg-white rounded-xl shadow-2xl w-full max-w-md overflow-hidden"
          >
            {/* Header */}
            <div className="p-6 border-b border-gray-100 flex items-center justify-between">
              <div className="flex items-center">
                <IconSettings className="w-6 h-6 text-dukeBlue mr-3" />
                <h2 className="text-xl text-dukeBlue font-header">Settings</h2>
              </div>
              <button 
                onClick={onClose}
                className="text-mountbattenPink hover:text-dukeBlue text-2xl w-8 h-8 flex items-center justify-center rounded-full hover:bg-gray-100 transition-all"
              >
                <IconX size={20} />
              </button>
            </div>

            {/* Content */}
            <div className="p-6">
              <div className="space-y-6">
                {/* Account Section */}
                <div>
                  <h3 className="text-sm text-dukeBlue mb-3 font-header">Account</h3>
                  {user ? (
                    <div className="space-y-4">
                      <div className="bg-gray-50 p-4 rounded-lg border">
                        <p className="text-xs text-mountbattenPink mb-1">
                          Signed in as
                        </p>
                        <p className="text-dukeBlue">
                          {user.email}
                        </p>
                      </div>
                      <button
                        onClick={handleSignOut}
                        className="flex items-center px-4 py-3 w-full bg-red-50 border border-red-200 text-red-600 hover:bg-red-100 hover:border-red-300 rounded-lg transition-all"
                      >
                        <IconLogout size={18} className="mr-3" />
                        Sign Out
                      </button>
                    </div>
                  ) : (
                    <div className="bg-gray-50 p-4 rounded-lg border text-center">
                      <p className="text-mountbattenPink">
                        Not signed in
                      </p>
                    </div>
                  )}
                </div>

                {/* App Info Section */}
                <div>
                  <h3 className="text-sm text-dukeBlue mb-3 font-header">Application</h3>
                  <div className="bg-gray-50 p-4 rounded-lg border">
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-sm text-mountbattenPink">Version</span>
                      <span className="text-sm text-dukeBlue">1.0.0</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-mountbattenPink">Status</span>
                      <span className="text-sm text-green-600">Active</span>
                    </div>
                  </div>
                </div>

                {/* Additional Settings Options */}
                <div>
                  <h3 className="text-sm text-dukeBlue mb-3 font-header">Preferences</h3>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border">
                      <span className="text-sm text-dukeBlue">Theme</span>
                      <span className="text-sm text-mountbattenPink">Auto</span>
                    </div>
                    <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border">
                      <span className="text-sm text-dukeBlue">Notifications</span>
                      <span className="text-sm text-mountbattenPink">Enabled</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Footer */}
            <div className="p-6 border-t border-gray-100 bg-gray-50">
              <button
                onClick={onClose}
                className="w-full px-4 py-3 bg-dukeBlue text-white text-sm rounded-lg hover:opacity-80 transition-opacity"
              >
                Close
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default SettingsModal;
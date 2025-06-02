'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '../chat/Auth';
import { IconLogout } from '@tabler/icons-react';
import { motion } from 'framer-motion';
import BackButton from '../components/backbutton';

export default function SettingsPage() {
  const { user, logOut } = useAuth();
  const router = useRouter();

  const handleSignOut = async () => {
    await logOut();
    router.push('/chat');
  };

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
      className="min-h-screen bg-neutral-900 text-white relative"
      initial="hidden"
      animate="visible"
      variants={pageAnimationVariants}
    >
      {/* Back button at top left */}
      <div className="absolute top-4 left-4 z-10">
        <BackButton 
          to="/chat"
          label="Back to Dashboard"
          variant="minimal"
          size="md"
        />
      </div>

      {/* Header */}
      <header className="bg-neutral-900 border-b border-neutral-700 p-6 pt-16">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-2xl font-serif text-blue-400 font-semibold">
            Settings
          </h1>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-2xl mx-auto p-6">
        <motion.section 
          variants={childAnimationVariants}
          className="mb-8 bg-neutral-800 rounded-lg p-6 shadow-sm border border-neutral-700"
        >
          <h2 className="text-xl font-semibold text-blue-400 mb-4 font-serif">
            Account
          </h2>
          {user ? (
            <div className="space-y-4">
              <div className="bg-neutral-700 p-4 rounded-lg border border-neutral-600">
                <p className="text-pink-400 text-sm">
                  Signed in as
                </p>
                <p className="font-medium text-blue-300">
                  {user.email}
                </p>
              </div>
              <button
                onClick={handleSignOut}
                className="flex items-center px-4 py-2 border border-pink-500 text-pink-400 hover:bg-pink-500 hover:text-white rounded-lg transition-colors font-medium"
              >
                <IconLogout size={18} className="mr-2" />
                Sign Out
              </button>
            </div>
          ) : (
            <p className="text-pink-400">
              Not signed in
            </p>
          )}
        </motion.section>

        <motion.section 
          variants={childAnimationVariants}
          className="bg-neutral-800 rounded-lg p-6 text-center text-pink-400 text-sm shadow-sm border border-neutral-700"
        >
          <p>
            Version 1.0.0
          </p>
        </motion.section>
      </main>
    </motion.div>
  );
}
'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '../chat/Auth';
import { IconLogout, IconArrowLeft } from '@tabler/icons-react';
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
      className="min-h-screen bg-neutral-900 text-white"
      initial="hidden"
      animate="visible"
      variants={pageAnimationVariants}
    >
      {/* Header */}
      <header className="bg-neutral-900 border-b border-trueBlue p-4 flex items-center">
        <BackButton />
        <h1 className="text-2xl font-serif text-dukeBlue font-semibold mx-auto pr-10">
          Settings
        </h1>
      </header>

      {/* Main content */}
      <main className="max-w-2xl mx-auto p-6">
        <motion.section 
          variants={childAnimationVariants}
          className="mb-8 bg-trueBlue rounded-lg p-6 shadow-sm"
        >
          <h2 className="text-xl font-semibold text-dukeBlue mb-4 font-serif">
            Account
          </h2>
          {user ? (
            <div className="space-y-4">
              <div className="bg-white p-4 rounded-lg border border-trueBlue">
                <p className="text-mountbattenPink text-sm">
                  Signed in as
                </p>
                <p className="font-medium text-dukeBlue">
                  {user.email}
                </p>
              </div>
              <button
                onClick={handleSignOut}
                className="flex items-center px-4 py-2 border border-mountbattenPink text-mountbattenPink hover:bg-mountbattenPink hover:text-white rounded-lg transition-colors font-medium"
              >
                <IconLogout size={18} className="mr-2" />
                Sign Out
              </button>
            </div>
          ) : (
            <p className="text-mountbattenPink">
              Not signed in
            </p>
          )}
        </motion.section>

        <motion.section 
          variants={childAnimationVariants}
          className="bg-trueBlue rounded-lg p-6 text-center text-mountbattenPink text-sm shadow-sm"
        >
          <p>
            Version 1.0.0
          </p>
        </motion.section>
      </main>
    </motion.div>
  );
}

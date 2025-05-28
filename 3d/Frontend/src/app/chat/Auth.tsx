'use client';

import { useState, useEffect } from 'react';
import { auth, provider } from '../firebase';
import { signInWithPopup, signOut, onAuthStateChanged, User } from 'firebase/auth';
import { IconBrandGoogle } from '@tabler/icons-react';

interface AuthProps {
  children?: React.ReactNode;
  onSignIn?: (user: User) => void;
}

export const useAuth = () => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (currentUser) => {
      setUser(currentUser);
      setLoading(false);
    });
    
    return () => unsubscribe();
  }, []);

  const signInWithGoogle = async () => {
    try {
      const result = await signInWithPopup(auth, provider);
      return result.user;
    } catch (error) {
      console.error("Error signing in with Google", error);
      return null;
    }
  };

  const logOut = async () => {
    try {
      await signOut(auth);
    } catch (error) {
      console.error("Error signing out", error);
    }
  };

  return { user, loading, signInWithGoogle, logOut };
};

export const AuthButton = ({ onSignIn }: AuthProps) => {
  const { user, signInWithGoogle, logOut } = useAuth();

  const handleSignIn = async () => {
    const user = await signInWithGoogle();
    if (user && onSignIn) {
      onSignIn(user);
    }
  };

  if (user) {
    return (
      <button 
        onClick={logOut}
        className="flex items-center justify-center gap-2 py-2 px-4 rounded-full bg-gray-200 dark:bg-neutral-700 hover:bg-gray-300 dark:hover:bg-neutral-600 transition-colors w-full"
      >
        <span className="text-sm">Sign Out</span>
      </button>
    );
  }

  return (
    <button 
      onClick={handleSignIn}
      className="flex items-center gap-2 py-2 px-4 rounded-full bg-white dark:bg-neutral-800 hover:bg-gray-100 dark:hover:bg-neutral-700 border border-gray-300 dark:border-neutral-600 transition-colors"
    >
      <IconBrandGoogle className="w-5 h-5 text-red-500" />
      <span className="text-sm">Sign in with Google</span>
    </button>
  );
};

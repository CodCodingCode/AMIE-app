'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import { auth, provider } from '../firebase'
import { signInWithPopup } from 'firebase/auth'
import { useRouter } from 'next/navigation'

interface AuthModalProps {
  isOpen: boolean
  onClose: () => void
  isEmbeddedInChat?: boolean
}

export default function AuthModal({ isOpen, onClose, isEmbeddedInChat = false }: AuthModalProps) {
  const router = useRouter()
  const [isLoggingIn, setIsLoggingIn] = useState(false)

  const handleGoogleSignIn = async () => {
    if (isLoggingIn) return
    
    try {
      setIsLoggingIn(true)
      await signInWithPopup(auth, provider)
      if (!isEmbeddedInChat) {
        router.push('/chat')
      }
    } catch (error) {
      console.error('Google login error:', error)
      setIsLoggingIn(false)
    }
  }

  if (!isOpen) return null

  return (
    <motion.div 
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
    >
      <motion.div 
        className="w-full max-w-md bg-[#2D2D2D] rounded-lg shadow-xl overflow-hidden"
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ type: 'spring', duration: 0.5 }}
      >
        <div className="p-6">
          <div className="text-center mb-6">
            <h2 className="text-2xl font-medium text-white mb-2">Welcome back</h2>
            <p className="text-gray-300 text-sm">
              Log in or sign up to get smarter responses, upload files and images, and more.
            </p>
          </div>
          
          <div className="space-y-4">
            <button 
              className="w-full bg-white text-gray-800 py-3 px-4 rounded-md font-medium flex items-center justify-center space-x-2 hover:bg-gray-100 transition"
              onClick={handleGoogleSignIn}
              disabled={isLoggingIn}
            >
              <svg className="w-5 h-5" viewBox="0 0 24 24">
                <path
                  fill="#4285F4"
                  d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                />
                <path
                  fill="#34A853"
                  d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                />
                <path
                  fill="#FBBC05"
                  d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                />
                <path
                  fill="#EA4335"
                  d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                />
              </svg>
              <span>{isLoggingIn ? 'Signing in...' : 'Continue with Google'}</span>
            </button>
          </div>
          
          <div className="text-center mt-6">
            <button 
              className="text-gray-400 text-sm hover:text-white"
              onClick={onClose}
            >
              Stay logged out
            </button>
          </div>
        </div>
      </motion.div>
    </motion.div>
  )
}

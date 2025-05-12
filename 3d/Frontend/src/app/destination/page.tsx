'use client'

import React from 'react'
import Link from 'next/link'

// Destination page that appears after portal transition
export default function DestinationPage() {
  return (
    <div className="h-screen w-full bg-gradient-to-b from-purple-900 to-black flex items-center justify-center text-white">
      <div className="text-center">
        <h1 className="text-5xl font-bold mb-6">Welcome to the New Dimension!</h1>
        <p className="text-xl mb-8">You've successfully traveled through the portal</p>
        <Link 
          href="/" 
          className="px-6 py-3 bg-purple-600 rounded-lg hover:bg-purple-700 transition-colors"
        >
          Return to Portal
        </Link>
      </div>
    </div>
  )
}
// components/Footer.tsx
'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

const Footer = () => {
  const pathname = usePathname();
  
  // Don't show footer on certain pages if needed
  const hideOnPaths = ['/loading', '/chat'];
  if (hideOnPaths.includes(pathname)) return null;

  return (
    <footer className="w-full py-16 px-8 md:px-16 bg-transparent">
      <div className="max-w-7xl mx-auto">
        {/* Logo and tagline */}
        <div className="flex items-center mb-12">
          <div className="text-3xl font-bold mr-2">bluebox</div>
          <div className="text-xl text-gray-500">ai</div>
        </div>
        
        {/* Main footer content - simplified grid with larger spacing */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-12 mb-16">
          <div>
            <p className="text-lg text-gray-500 max-w-xs leading-relaxed">
              Bluebox, derived from beyond the box thinking,
              is a general AI agent that turns your thoughts into actions.
            </p>
            <p className="text-lg text-gray-500 mt-4">© 2024 Bluebox AI</p>
          </div>
          
          {/* Community Column - larger text and spacing */}
          <div>
            <h3 className="text-xl font-medium mb-6">Community</h3>
            <ul className="space-y-4">
              <li><Link href="/events" className="text-lg text-gray-600 hover:text-gray-900">Events</Link></li>
              <li><Link href="/campus" className="text-lg text-gray-600 hover:text-gray-900">Campus</Link></li>
              <li><Link href="/fellows" className="text-lg text-gray-600 hover:text-gray-900">Fellows</Link></li>
            </ul>
          </div>
          
          {/* Company Column - larger text and spacing */}
          <div>
            <h3 className="text-xl font-medium mb-6">Company</h3>
            <ul className="space-y-4">
              <li><Link href="/feedback" className="text-lg text-gray-600 hover:text-gray-900">Feedback</Link></li>
              <li><Link href="/media" className="text-lg text-gray-600 hover:text-gray-900">Media Inquiries</Link></li>
              <li><Link href="/contact" className="text-lg text-gray-600 hover:text-gray-900">Contact us</Link></li>
            </ul>
          </div>
          
          {/* Resources Column - larger text and spacing */}
          <div>
            <h3 className="text-xl font-medium mb-6">Resources</h3>
            <ul className="space-y-4">
              <li><Link href="/privacy" className="text-lg text-gray-600 hover:text-gray-900">Privacy policy</Link></li>
              <li><Link href="/terms" className="text-lg text-gray-600 hover:text-gray-900">Terms of service</Link></li>
            </ul>
          </div>
        </div>
        
        {/* Social links and quote - simplified with larger icons */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center pt-8 border-t border-gray-200">
          <div className="flex space-x-6 mb-6 md:mb-0">
            <a href="https://linkedin.com" target="_blank" rel="noopener noreferrer" aria-label="LinkedIn">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor" className="text-gray-600 hover:text-gray-900">
                <path d="M19 3a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h14m-.5 15.5v-5.3a3.26 3.26 0 0 0-3.26-3.26c-.85 0-1.84.52-2.32 1.3v-1.11h-2.79v8.37h2.79v-4.93c0-.77.62-1.4 1.39-1.4a1.4 1.4 0 0 1 1.4 1.4v4.93h2.79M6.88 8.56a1.68 1.68 0 0 0 1.68-1.68c0-.93-.75-1.69-1.68-1.69a1.69 1.69 0 0 0-1.69 1.69c0 .93.76 1.68 1.69 1.68m1.39 9.94v-8.37H5.5v8.37h2.77z"></path>
              </svg>
            </a>
            <a href="https://twitter.com" target="_blank" rel="noopener noreferrer" aria-label="Twitter">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor" className="text-gray-600 hover:text-gray-900">
                <path d="M18.901 1.153h3.68l-8.04 9.19L24 22.846h-7.406l-5.8-7.584-6.638 7.584H.474l8.6-9.83L0 1.154h7.594l5.243 6.932ZM17.61 20.644h2.039L6.486 3.24H4.298Z"></path>
              </svg>
            </a>
            <a href="https://youtube.com" target="_blank" rel="noopener noreferrer" aria-label="YouTube">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor" className="text-gray-600 hover:text-gray-900">
                <path d="M10 15l5.19-3L10 9v6m11.56-7.83c.13.47.22 1.1.28 1.9.07.8.1 1.49.1 2.09L22 12c0 2.19-.16 3.8-.44 4.83-.25.9-.83 1.48-1.73 1.73-.47.13-1.33.22-2.65.28-1.3.07-2.49.1-3.59.1L12 19c-4.19 0-6.8-.16-7.83-.44-.9-.25-1.48-.83-1.73-1.73-.13-.47-.22-1.1-.28-1.9-.07-.8-.1-1.49-.1-2.09L2 12c0-2.19.16-3.8.44-4.83.25-.9.83-1.48 1.73-1.73.47-.13 1.33-.22 2.65-.28 1.3-.07 2.49-.1 3.59-.1L12 5c4.19 0 6.8.16 7.83.44.9.25 1.48.83 1.73 1.73z"></path>
              </svg>
            </a>
          </div>
          
          <div className="text-gray-500 text-xl italic">
            "Less structure, more intelligence."
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
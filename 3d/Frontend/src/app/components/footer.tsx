// components/Footer.tsx
'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import Image from 'next/image';

const navigationLinks = [
  { href: '/', label: 'Home' },
  { href: '/platform', label: 'Platform' },
  { href: '/solutions', label: 'Solutions' },
  { href: '/company', label: 'Company' },
  { href: '/contact', label: 'Contact Us' }
];

const footerLinks = [
  { href: '/privacy', label: 'Privacy Policy' },
  { href: '/terms', label: 'Terms & Conditions' }
];

const Footer = () => {
  const pathname = usePathname();
  
  // Don't show footer on certain pages
  const hideOnPaths = ['/loading', '/chat'];
  if (hideOnPaths.includes(pathname)) return null;

  return (
    <section id="footer" className="w-full px-8 md:px-16 bg-neutral-900 text-white">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between">
        {/* Left side - Logo and mission */}
        <div className="md:w-1/3 mb-12 md:mb-0 pr-8">
          <div className="mb-6">
            <Image src="/reallogo.png" alt="Bluebox Logo" width={100} height={40} />
          </div>
          <p className="text-base mb-8 leading-relaxed">
            Our mission is to democratize computational intelligence
            tools and empower researchers and
            organizations worldwide.
          </p>
          
          {/* Social Links */}
          <div className="flex space-x-4 mb-4">
            <Link 
              href="https://linkedin.com" 
              className="w-8 h-8 rounded-full border border-white flex items-center justify-center hover:bg-white hover:text-neutral-900 transition-colors"
              aria-label="LinkedIn"
            >
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
                <path d="M19 3a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h14m-.5 15.5v-5.3a3.26 3.26 0 0 0-3.26-3.26c-.85 0-1.84.52-2.32 1.3v-1.11h-2.79v8.37h2.79v-4.93c0-.77.62-1.4 1.39-1.4a1.4 1.4 0 0 1 1.4 1.4v4.93h2.79M6.88 8.56a1.68 1.68 0 0 0 1.68-1.68c0-.93-.75-1.69-1.68-1.69a1.69 1.69 0 0 0-1.69 1.69c0 .93.76 1.68 1.69 1.68m1.39 9.94v-8.37H5.5v8.37h2.77z"></path>
              </svg>
            </Link>
          </div>
        </div>
        
        {/* Right side - Navigation Links */}
        <div className="w-full md:w-2/3 flex flex-col gap-4 md:items-end">
          {navigationLinks.map(({ href, label }) => (
            <div key={href}>
              <h3 className="text-xl mb-4 font-header">
                <Link href={href} className="hover:opacity-80 transition-opacity">
                  {label}
                </Link>
              </h3>
            </div>
          ))}
        </div>
      </div>
      
      {/* Footer bottom - Copyright and links */}
      <div className="max-w-7xl mx-auto mt-16 pt-8 border-t border-white flex flex-col md:flex-row justify-between items-center mb-16">
        <div className="text-sm opacity-70 mb-4 md:mb-0">
          Copyright 2024© bluebox.ai All Rights Reserved
        </div>
        <div className="flex space-x-6 text-sm opacity-70">
          {footerLinks.map(({ href, label }) => (
            <Link 
              key={href}
              href={href} 
              className="hover:opacity-100 transition-opacity"
            >
              {label}
            </Link>
          ))}
        </div>
      </div>
    </section>
  );
};

export default Footer;

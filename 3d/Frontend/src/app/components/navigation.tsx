'use client';

import { motion, AnimatePresence } from 'framer-motion';
import Link from 'next/link';
import Image from 'next/image';
import { IconMenu2, IconX } from '@tabler/icons-react';
import { useScrollEffect, useMobileMenu, useBlueboxAnimation } from '@/app/lib/hooks';
import { slideDown, fadeInUp, quickTransition } from '@/app/lib/utils';

export default function Navigation() {
  const isScrolled = useScrollEffect(50);
  const { isOpen: isMobileMenuOpen, toggle: toggleMobileMenu, close: closeMobileMenu } = useMobileMenu();
  const { isAnimationStarted, handleGetStartedClick } = useBlueboxAnimation();

  const navLinks = [
    { href: '#features', label: 'Features' },
    { href: '#benefits', label: 'Benefits' },
    { href: '#testimonials', label: 'Testimonials' }
  ];

  const handleMobileGetStarted = () => {
    closeMobileMenu();
    handleGetStartedClick();
  };

  return (
    <>
      <motion.nav
        variants={slideDown}
        initial="initial"
        animate="animate"
        transition={quickTransition}
        className={`fixed top-0 left-0 right-0 z-50 transition-all duration-500 ${
          isScrolled ? 'bg-neutral-900/95 backdrop-blur-md' : 'bg-transparent'
        } ${
          isAnimationStarted ? 'opacity-0 pointer-events-none' : 'opacity-100'
        }`}
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-20">
            {/* Logo */}
            <Link href="/" className="flex items-center">
              <Image
                src="/reallogo.png"
                alt="Bluebox Logo"
                width={40}
                height={40}
                className="h-10 w-auto"
              />
              <span className="ml-3 text-xl font-bold text-white">Bluebox</span>
            </Link>

            {/* Desktop Navigation */}
            <div className="hidden md:flex items-center space-x-8">
              {navLinks.map(({ href, label }) => (
                <Link
                  key={href}
                  href={href}
                  className="text-gray-300 hover:text-white transition-colors"
                >
                  {label}
              </Link>
              ))}
              <button 
                onClick={handleGetStartedClick}
                className="bg-blue-600 text-white px-6 py-2 rounded-full hover:bg-blue-700 transition-colors"
              >
                Get Started
              </button>
            </div>

            {/* Mobile menu button */}
            <button
              className="md:hidden text-gray-300 hover:text-white"
              onClick={toggleMobileMenu}
              aria-label="Toggle mobile menu"
            >
              {isMobileMenuOpen ? <IconX className="h-6 w-6" /> : <IconMenu2 className="h-6 w-6" />}
            </button>
          </div>
        </div>
      </motion.nav>

      {/* Mobile menu */}
      <AnimatePresence>
        {isMobileMenuOpen && !isAnimationStarted && (
          <motion.div
            variants={fadeInUp}
            initial="initial"
            animate="animate"
            exit="exit"
            transition={quickTransition}
            className="fixed inset-0 z-40 bg-neutral-900 md:hidden"
          >
            <div className="pt-20 p-4">
              <div className="flex flex-col space-y-4">
                {navLinks.map(({ href, label }) => (
                <Link
                    key={href}
                    href={href}
                  className="text-gray-300 hover:text-white transition-colors text-lg py-2"
                    onClick={closeMobileMenu}
                >
                    {label}
                </Link>
                ))}
                <button
                  onClick={handleMobileGetStarted}
                  className="bg-blue-600 text-white px-6 py-3 rounded-full text-center hover:bg-blue-700 transition-colors"
                >
                  Get Started
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
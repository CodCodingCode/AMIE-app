// components/BackButton.tsx
'use client';

import { useRouter } from 'next/navigation';
import { IconArrowLeft } from '@tabler/icons-react';
import { cn } from '@/app/lib/utils';

interface BackButtonProps {
  to?: string;
  label?: string;
  variant?: 'default' | 'minimal' | 'outlined' | 'floating';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export default function BackButton({ 
  to, 
  label = 'Back',
  variant = 'default',
  size = 'md',
  className = ''
}: BackButtonProps) {
  const router = useRouter();

  const handleBack = () => {
    if (to) {
      router.push(to);
    } else {
      router.back();
    }
  };

  const baseClasses = "inline-flex items-center font-medium transition-colors duration-200 focus:outline-none";
  
  const sizeClasses = {
    sm: "px-2 py-1 text-sm gap-1",
    md: "px-3 py-2 text-sm gap-2", 
    lg: "px-4 py-2 text-base gap-2"
  };

  const iconSizes = {
    sm: 14,
    md: 16,
    lg: 18
  };

  const variantClasses = {
    default: `
      text-gray-300 hover:text-white
      hover:bg-gray-800 rounded-lg
    `,
    minimal: `
      text-gray-300 hover:text-white
      hover:bg-gray-800/50 rounded-lg
    `,
    outlined: `
      border border-gray-600 text-gray-300
      hover:bg-gray-800 hover:text-white
      rounded-lg
    `,
    floating: `
      bg-gray-800 text-gray-300
      hover:bg-gray-700 hover:text-white
      rounded-lg shadow-sm
    `
  };

  return (
    <button 
      onClick={handleBack}
      className={cn(
        baseClasses,
        sizeClasses[size],
        variantClasses[variant],
        className
      )}
    >
      <IconArrowLeft size={iconSizes[size]} />
      <span>{label}</span>
    </button>
  );
}
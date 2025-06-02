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

  const baseClasses = "inline-flex items-center justify-center font-medium transition-all duration-200 ease-out focus:outline-none focus:ring-2 focus:ring-offset-2 active:scale-95";
  
  const sizeClasses = {
    sm: "px-3 py-1.5 text-sm gap-1.5",
    md: "px-4 py-2 text-sm gap-2", 
    lg: "px-6 py-3 text-base gap-2.5"
  };

  const iconSizes = {
    sm: 16,
    md: 18,
    lg: 20
  };

  const variantClasses = {
    default: `
      bg-white/80 backdrop-blur-sm border border-gray-200/60 
      text-gray-700 hover:text-blue-600 
      hover:bg-white hover:border-gray-300 hover:shadow-md
      focus:ring-blue-500/20 rounded-xl
      shadow-sm hover:shadow-lg
    `,
    minimal: `
      text-gray-700 hover:text-blue-600
      hover:bg-gray-50/80 rounded-lg
      focus:ring-blue-500/20
    `,
    outlined: `
      border-2 border-blue-600 text-blue-600
      hover:bg-blue-600 hover:text-white hover:border-blue-600
      focus:ring-blue-500/20 rounded-xl
      shadow-sm hover:shadow-md
    `,
    floating: `
      bg-white/90 backdrop-blur-md border border-gray-200/50
      text-gray-700 hover:text-blue-600
      hover:bg-white hover:shadow-xl hover:scale-105
      focus:ring-blue-500/20 rounded-full
      shadow-lg hover:shadow-2xl
    `
  };

  return (
    <button 
      onClick={handleBack}
      className={cn(
        baseClasses,
        sizeClasses[size],
        variantClasses[variant],
        "group",
        className
      )}
    >
      <IconArrowLeft 
        size={iconSizes[size]} 
        className="transition-transform duration-200 group-hover:-translate-x-0.5" 
      />
      <span className="font-medium">{label}</span>
    </button>
  );
}
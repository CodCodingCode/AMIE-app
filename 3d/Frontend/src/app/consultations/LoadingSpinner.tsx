'use client';

import React from 'react';

interface LoadingSpinnerProps {
  message?: string;
  size?: 'sm' | 'md' | 'lg';
}

const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({ message, size = 'md' }) => {
  const sizeClasses = {
    sm: 'h-6 w-6',
    md: 'h-8 w-8',
    lg: 'h-12 w-12',
  };

  return (
    <div className="flex flex-col justify-center items-center h-full">
      <div className={`animate-spin rounded-full border-b-2 border-dukeBlue ${sizeClasses[size]}`}></div>
      {message && <p className="mt-3 text-sm text-gray-400">{message}</p>}
    </div>
  );
};

export default LoadingSpinner; 
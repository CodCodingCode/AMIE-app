'use client';

import React from 'react';

interface CleanLoadingSpinnerProps {
  message?: string;
  size?: 'sm' | 'md' | 'lg';
}

const CleanLoadingSpinner: React.FC<CleanLoadingSpinnerProps> = ({ 
  message, 
  size = 'md' 
}) => {
  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-6 w-6',
    lg: 'h-8 w-8',
  };

  return (
    <div className="flex flex-col items-center justify-center">
      <div className={`animate-spin rounded-full border-2 border-gray-300 border-t-blue-600 ${sizeClasses[size]}`}></div>
      {message && (
        <p className="mt-3 text-sm text-gray-600">{message}</p>
      )}
    </div>
  );
};

export default CleanLoadingSpinner;
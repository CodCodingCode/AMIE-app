'use client';

import React from 'react';
import { IconStethoscope, type Icon as TablerIconType } from '@tabler/icons-react';

interface EmptyStateProps {
  icon?: TablerIconType;
  title: string;
  message: string;
  actionButton?: React.ReactNode;
}

const EmptyState: React.FC<EmptyStateProps> = ({ 
  icon: IconComponent = IconStethoscope,
  title, 
  message, 
  actionButton 
}) => {
  return (
    <div className="p-8 text-center flex flex-col items-center justify-center h-full">
      <IconComponent className="w-12 h-12 mx-auto text-gray-600 mb-4" />
      <h3 className="text-lg font-medium text-gray-300 mb-2">
        {title}
      </h3>
      <p className="text-sm text-gray-500 mb-4">
        {message}
      </p>
      {actionButton}
    </div>
  );
};

export default EmptyState; 
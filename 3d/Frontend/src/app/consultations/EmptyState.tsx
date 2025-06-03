'use client';

import React from 'react';

interface CleanEmptyStateProps {
  title: string;
  message: string;
  actionText?: string;
  onAction?: () => void;
}

const CleanEmptyState: React.FC<CleanEmptyStateProps> = ({ 
  title, 
  message, 
  actionText,
  onAction 
}) => {
  return (
    <div className="text-center py-8">
      <h3 className="text-lg font-medium text-gray-900 mb-2">
        {title}
      </h3>
      <p className="text-sm text-gray-600 mb-4">
        {message}
      </p>
      {actionText && onAction && (
        <button
          onClick={onAction}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-md transition-colors"
        >
          {actionText}
        </button>
      )}
    </div>
  );
};

export default CleanEmptyState;
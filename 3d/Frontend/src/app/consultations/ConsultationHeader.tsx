'use client';

import React from 'react';

interface UltraSimpleHeaderProps {
  onBack: () => void;
  onBook: () => void;
}

const UltraSimpleHeader: React.FC<UltraSimpleHeaderProps> = ({ onBack, onBook }) => {
  return (
    <div className="bg-white rounded-xl p-6 flex items-center justify-between shadow-lg">
      <button 
        onClick={onBack}
        className="text-dukeBlue text-sm hover:underline"
      >
        ← Back
      </button>
      
      <h1 className="text-dukeBlue text-xl font-serif">Consultations</h1>
      
      <button 
        onClick={onBook}
        className="bg-dukeBlue text-white px-6 py-3 text-sm rounded-lg hover:opacity-80 transition-opacity"
      >
        Book $29
      </button>
    </div>
  );
};

export default UltraSimpleHeader;
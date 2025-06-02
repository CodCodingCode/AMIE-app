'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import BackButton from '../components/backbutton';
import { IconPlus } from '@tabler/icons-react';

interface ConsultationHeaderProps {
  title: string;
  onNewConsultationClick: () => void;
}

const ConsultationHeader: React.FC<ConsultationHeaderProps> = ({ title, onNewConsultationClick }) => {
  return (
    <header className="bg-neutral-900 border-b border-neutral-800 p-6">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        <div className="flex items-center">
          <BackButton
            to="/chat"
            label="Back to Chat"
            variant="minimal"
            size="md"
            className="mr-4"
          />
          <h1 className="text-2xl font-serif text-white font-semibold">
            {title}
          </h1>
        </div>
        <button
          onClick={onNewConsultationClick}
          className="px-4 py-2 bg-dukeBlue hover:bg-dukeBlue/80 text-white rounded-lg transition-colors flex items-center text-sm font-medium"
        >
          <IconPlus className="w-4 h-4 mr-2" />
          New Consultation
        </button>
      </div>
    </header>
  );
};

export default ConsultationHeader; 
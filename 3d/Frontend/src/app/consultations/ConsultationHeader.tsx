'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import BackButton from '../components/backbutton';
import { IconPlus, IconCreditCard } from '@tabler/icons-react';

interface ConsultationHeaderProps {
  title: string;
  onNewConsultationClick: () => void;
}

const ConsultationHeader: React.FC<ConsultationHeaderProps> = ({ title, onNewConsultationClick }) => {
  const router = useRouter();

  const handleBookConsultation = async () => {
    try {
      // Create checkout session directly
      const response = await fetch('/api/create-checkout-session', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          quantity: 1,
          metadata: {
            consultation_type: 'bluebox_live',
            return_url: '/consultations'
          }
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to create checkout session');
      }

      const session = await response.json();
      
      // Redirect to Stripe Checkout
      window.location.href = session.url;
    } catch (err) {
      console.error('Error creating checkout session:', err);
      alert('Unable to start payment process. Please try again.');
    }
  };

  return (
    <div className="relative">
      {/* Back button at top left */}
      <div className="absolute top-4 left-4 z-10">
        <BackButton
          to="/chat"
          label="Back to Chat"
          variant="minimal"
          size="md"
        />
      </div>
      
      {/* Main header content */}
      <header className="bg-neutral-900 border-b border-neutral-800 p-6 pt-16">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <h1 className="text-2xl font-serif text-white font-semibold">
            {title}
          </h1>
          
          {/* Button group */}
          <div className="flex items-center space-x-3">
            <button
              onClick={handleBookConsultation}
              className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors flex items-center text-sm font-medium"
            >
              <IconCreditCard className="w-4 h-4 mr-2" />
              Book Consultation - $29 CAD
            </button>
            
            <button
              onClick={onNewConsultationClick}
              className="px-4 py-2 bg-dukeBlue hover:bg-dukeBlue/80 text-white rounded-lg transition-colors flex items-center text-sm font-medium"
            >
              <IconPlus className="w-4 h-4 mr-2" />
              New Consultation
            </button>
          </div>
        </div>
      </header>
    </div>
  );
};

export default ConsultationHeader;
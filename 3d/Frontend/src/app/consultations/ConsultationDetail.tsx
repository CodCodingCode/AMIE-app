'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { Chat, ChatMessage } from '../chat/chatService';
import EmptyState from './EmptyState';
import { 
  IconFileText, 
  IconSend, 
  IconLoader, 
  IconUser, 
  IconSparkles,
  IconCalendarEvent,
  IconNotes,
  IconPaperclip,
  IconCreditCard
} from '@tabler/icons-react';
import { formatDate as originalFormatDate } from '@/app/lib/utils'; 

const formatDateUtil: (date: Date | string | number, formatStr?: string) => string = originalFormatDate;

interface ConsultationDetailProps {
  selectedChat: Chat | null;
  onGenerateSOAP: () => void;
  onCreateReferral: () => void;
  isGeneratingSOAP: boolean;
  isCreatingReferral: boolean;
}

const MessageBubble: React.FC<{ message: ChatMessage, isLast: boolean }> = ({ message, isLast }) => {
  const isUser = message.sender === 'user';
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: isLast ? 0.1 : 0 }}
      className={`flex mb-4 ${isUser ? 'justify-end' : 'justify-start'}`}
    >
      <div className={`p-3 rounded-lg max-w-lg lg:max-w-xl shadow-md ${isUser 
        ? 'bg-blue-600 text-white rounded-br-none' 
        : 'bg-neutral-700 text-gray-200 rounded-bl-none'
      }`}>
        <p className="text-sm whitespace-pre-wrap">{message.text}</p>
        {message.timestamp && (
          <p className={`text-xs mt-1 ${isUser ? 'text-blue-200' : 'text-gray-400'} text-right`}>
            {formatDateUtil(message.timestamp, 'PPpp')} 
          </p>
        )}
      </div>
    </motion.div>
  );
};

const ConsultationDetail: React.FC<ConsultationDetailProps> = ({ 
  selectedChat, 
  onGenerateSOAP, 
  onCreateReferral,
  isGeneratingSOAP,
  isCreatingReferral
}) => {
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

  if (!selectedChat) {
    return (
      <div className="col-span-12 md:col-span-7 lg:col-span-8 xl:col-span-9 bg-neutral-800 rounded-xl border border-neutral-700 flex flex-col h-full">
        <EmptyState 
          icon={IconNotes}
          title="No Consultation Selected"
          message="Please select a consultation from the list to view its details."
          actionButton={
            <button 
              onClick={handleBookConsultation}
              className="mt-4 px-6 py-3 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors flex items-center gap-2 mx-auto"
            >
              <IconCreditCard className="w-4 h-4" />
              Book New Consultation - $29 CAD
            </button>
          }
        />
      </div>
    );
  }

  const { title, messages, metadata, createdAt, updatedAt } = selectedChat;

  return (
    <div className="col-span-12 md:col-span-7 lg:col-span-8 xl:col-span-9 bg-neutral-800 rounded-xl border border-neutral-700 flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b border-neutral-700">
        <h2 className="text-lg font-semibold text-white truncate">{title || 'Untitled Consultation'}</h2>
        <div className="flex items-center space-x-3 text-xs text-gray-400 mt-1">
            <span>Created: {formatDateUtil(createdAt, 'PPP')}</span>
            <span>Last Update: {formatDateUtil(updatedAt, 'PPP p')}</span>
            {metadata && (
                <span className="px-2 py-0.5 bg-neutral-700 rounded-full text-neutral-300 text-xs capitalize">
                    Status: {metadata.status}
                </span>
            )}
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-grow p-4 overflow-y-auto no-scrollbar">
        <AnimatePresence>
          {messages.map((msg, index) => (
            <MessageBubble key={index} message={msg} isLast={index === messages.length - 1}/>
          ))}
        </AnimatePresence>
        {messages.length === 0 && (
            <EmptyState 
                icon={IconSparkles}
                title="No messages in this consultation yet."
                message="The conversation will appear here once messages are exchanged."
            />
        )}
      </div>

      {/* Actions Footer */}
      <div className="p-4 border-t border-neutral-700 bg-neutral-800/70 backdrop-blur-sm">
        <div className="flex flex-col space-y-3">
          {/* First row - Payment button */}
          <button
            onClick={handleBookConsultation}
            className="w-full px-4 py-2.5 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors flex items-center justify-center text-sm font-medium"
          >
            <IconCreditCard className="w-4 h-4 mr-2" />
            Book New Consultation - $29 CAD
          </button>
          
          {/* Second row - SOAP and Referral buttons */}
          <div className="flex flex-col sm:flex-row sm:items-center sm:space-x-3 space-y-3 sm:space-y-0">
            <button
              onClick={onGenerateSOAP}
              disabled={isGeneratingSOAP || messages.length === 0}
              className="flex-1 px-4 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors flex items-center justify-center text-sm font-medium disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {isGeneratingSOAP ? (
                <><IconLoader className="w-4 h-4 mr-2 animate-spin" /> Generating...</>
              ) : (
                <><IconFileText className="w-4 h-4 mr-2" /> Generate SOAP Note</>
              )}
            </button>
            <button
              onClick={onCreateReferral}
              disabled={isCreatingReferral || messages.length === 0}
              className="flex-1 px-4 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg transition-colors flex items-center justify-center text-sm font-medium disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {isCreatingReferral ? (
                <><IconLoader className="w-4 h-4 mr-2 animate-spin" /> Creating...</>
              ) : (
                <><IconSend className="w-4 h-4 mr-2" /> Create Referral</>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ConsultationDetail;
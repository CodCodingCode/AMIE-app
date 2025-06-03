'use client';

import React from 'react';
import { Chat, ChatMessage } from '../chat/chatService';

interface UltraSimpleDetailProps {
  selectedChat: Chat | null;
  onGenerateSOAP: () => void;
  onCreateReferral: () => void;
  isGeneratingSOAP: boolean;
  isCreatingReferral: boolean;
  onBookConsultation: () => void;
}

const Message: React.FC<{ message: ChatMessage }> = ({ message }) => {
  const isUser = message.sender === 'user';
  
  return (
    <div className={`mb-6 ${isUser ? 'text-right' : 'text-left'}`}>
      <div className={`inline-block max-w-xs lg:max-w-md p-4 text-sm rounded-xl ${
        isUser 
          ? 'bg-dukeBlue text-white' 
          : 'bg-gray-50 text-dukeBlue border border-gray-200'
      }`}>
        <div className="whitespace-pre-wrap">{message.text}</div>
        {message.timestamp && (
          <div className={`text-xs mt-2 ${
            isUser ? 'text-white opacity-70' : 'text-mountbattenPink'
          }`}>
            {new Date(message.timestamp).toLocaleTimeString([], { 
              hour: '2-digit', 
              minute: '2-digit' 
            })}
          </div>
        )}
      </div>
    </div>
  );
};

const UltraSimpleDetail: React.FC<UltraSimpleDetailProps> = ({ 
  selectedChat, 
  onGenerateSOAP, 
  onCreateReferral,
  isGeneratingSOAP,
  isCreatingReferral,
  onBookConsultation
}) => {
  if (!selectedChat) {
    return (
      <div className="flex-1 bg-white rounded-xl shadow-lg flex items-center justify-center">
        <div className="text-center">
          <div className="text-dukeBlue text-xl mb-4">Select a consultation</div>
          <button
            onClick={onBookConsultation}
            className="bg-dukeBlue text-white px-6 py-3 text-sm rounded-lg hover:opacity-80 transition-opacity"
          >
            Book New - $29
          </button>
        </div>
      </div>
    );
  }

  const { title, messages, createdAt } = selectedChat;

  return (
    <div className="flex-1 bg-white rounded-xl shadow-lg flex flex-col overflow-hidden">
      {/* Header */}
      <div className="p-6 border-b border-gray-100">
        <div className="text-xl font-medium text-dukeBlue mb-2">
          {title || 'Untitled Consultation'}
        </div>
        <div className="text-sm text-mountbattenPink">
          {new Date(createdAt).toLocaleDateString()}
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 p-6 overflow-y-auto">
        {messages.length === 0 ? (
          <div className="text-center text-dukeBlue mt-8">
            No messages yet
          </div>
        ) : (
          messages.map((msg, index) => (
            <Message key={index} message={msg} />
          ))
        )}
      </div>

      {/* Actions */}
      <div className="p-6 border-t border-gray-100">
        <div className="space-y-4">
          <button
            onClick={onBookConsultation}
            className="w-full bg-dukeBlue text-white py-3 text-sm rounded-lg hover:opacity-80 transition-opacity"
          >
            Book New Consultation - $29
          </button>
          
          <div className="grid grid-cols-2 gap-4">
            <button
              onClick={onGenerateSOAP}
              disabled={isGeneratingSOAP || messages.length === 0}
              className="bg-trueBlue text-dukeBlue py-3 text-sm rounded-lg border border-mountbattenPink hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            >
              {isGeneratingSOAP ? 'Generating...' : 'SOAP Note'}
            </button>
            
            <button
              onClick={onCreateReferral}
              disabled={isCreatingReferral || messages.length === 0}
              className="bg-trueBlue text-dukeBlue py-3 text-sm rounded-lg border border-mountbattenPink hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            >
              {isCreatingReferral ? 'Creating...' : 'Referral'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default UltraSimpleDetail;
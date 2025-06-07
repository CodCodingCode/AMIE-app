'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '../chat/Auth';
import { chatService, Chat, SOAPNote, Referral } from '../chat/chatService';
import { IconMessage, IconSearch, IconArrowLeft, IconPlus, IconFileText, IconUsers, IconLoader } from '@tabler/icons-react';
import { cn } from '@/app/lib/utils';

const EmptyState = ({ title, message, actionText, onAction }: {
  title: string;
  message: string;
  actionText?: string;
  onAction?: () => void;
}) => (
  <div className="text-center py-12 px-6 flex flex-col items-center justify-center h-full text-gray-400">
    <h3 className="text-lg text-gray-300 mb-2 font-header">{title}</h3>
    <p className="text-sm text-gray-500 mb-6 max-w-xs">{message}</p>
    {actionText && onAction && (
      <button onClick={onAction} className="px-6 py-2 bg-blue-500 hover:bg-blue-600 text-white text-sm rounded-lg transition-colors flex items-center">
        <IconPlus size={18} className="mr-2" />
        {actionText}
      </button>
    )}
  </div>
);

const ConsultationItem = ({ chat, isSelected, onSelect }: {
  chat: Chat;
  isSelected: boolean;
  onSelect: () => void;
}) => {
  const formatDate = (date: Date) => {
    const diffInHours = Math.floor((Date.now() - date.getTime()) / (1000 * 60 * 60));
    if (diffInHours < 24) return `${diffInHours}h ago`;
    const diffInDays = Math.floor(diffInHours / 24);
    if (diffInDays < 7) return `${diffInDays}d ago`;
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  const getPreview = () => {
    const lastMessage = chat.messages[chat.messages.length - 1];
    return lastMessage?.text?.slice(0, 60) + (lastMessage?.text?.length > 60 ? '...' : '') || 'No messages';
  };

  return (
    <div
      onClick={onSelect}
      className={cn(
        "p-4 border-b border-gray-700 cursor-pointer hover:bg-gray-700 transition-colors rounded-lg mb-2",
        isSelected && "bg-blue-600/30 border-l-4 border-blue-500"
      )}
    >
      <div className="flex items-center justify-between mb-1.5">
        <h4 className="text-sm text-gray-100 truncate flex-1 font-header">
          {chat.title || 'Untitled Consultation'}
        </h4>
        <span className="text-xs text-gray-400">{formatDate(chat.updatedAt)}</span>
      </div>
      <p className="text-xs text-gray-500 mb-2 truncate">{getPreview()}</p>
      <div className="flex items-center text-xs text-gray-500">
        <IconMessage className="w-3.5 h-3.5 mr-1.5" />
        <span>{chat.messages.length} messages</span>
      </div>
    </div>
  );
};

const Modal = ({ isOpen, onClose, title, children, actions }: {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
  actions?: React.ReactNode;
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/80 flex items-center justify-center p-4 z-50" onClick={onClose}>
      <div className="bg-gray-800 w-full max-w-2xl max-h-[90vh] rounded-xl shadow-2xl border border-gray-700 flex flex-col" onClick={(e) => e.stopPropagation()}>
        <div className="p-5 border-b border-gray-700 flex items-center justify-between">
          <h2 className="text-lg text-gray-100 font-header">{title}</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-200 text-2xl">×</button>
        </div>
        <div className="p-5 overflow-y-auto flex-1">{children}</div>
        {actions && <div className="p-5 border-t border-gray-700 flex justify-end gap-3">{actions}</div>}
      </div>
    </div>
  );
};

export default function ConsultationsPage() {
  const router = useRouter();
  const { user, loading: authLoading } = useAuth();
  
  const [chats, setChats] = useState<Chat[]>([]);
  const [filteredChats, setFilteredChats] = useState<Chat[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedChat, setSelectedChat] = useState<Chat | null>(null);
  const [isGeneratingSOAP, setIsGeneratingSOAP] = useState(false);
  const [isCreatingReferral, setIsCreatingReferral] = useState(false);
  const [currentSOAP, setCurrentSOAP] = useState<SOAPNote | null>(null);
  const [currentReferral, setCurrentReferral] = useState<Referral | null>(null);

  useEffect(() => {
    if (user) {
      chatService.getUserChats(user).then(userChats => {
        const nonEmptyChats = userChats
          .filter(chat => chat.messages?.length > 0)
          .sort((a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime());
        setChats(nonEmptyChats);
        setFilteredChats(nonEmptyChats);
        if (nonEmptyChats.length > 0) setSelectedChat(nonEmptyChats[0]);
        setIsLoading(false);
      });
    }
  }, [user]);

  useEffect(() => {
    const filtered = searchTerm
      ? chats.filter(chat => chat.title.toLowerCase().includes(searchTerm.toLowerCase()))
      : chats;
    setFilteredChats(filtered);
    if (selectedChat && !filtered.find(c => c.id === selectedChat.id)) {
      setSelectedChat(filtered[0] || null);
    }
  }, [chats, searchTerm, selectedChat]);

  const handleAction = async (action: string, setLoading: (loading: boolean) => void, setResult: (result: any) => void) => {
    if (!selectedChat) return;
    setLoading(true);
    try {
      const response = await fetch('/api/consultations', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action, chatData: selectedChat })
      });
      const result = await response.json();
      if (response.ok) {
        setResult(result[action === 'generateSOAP' ? 'soapNote' : 'referral']);
      } else {
        throw new Error(result.error);
      }
    } catch (error: any) {
      alert(`Error: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const downloadText = (content: string, filename: string) => {
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (authLoading) {
    return (
      <div className="h-screen bg-gray-900 flex items-center justify-center">
        <IconLoader size={48} className="animate-spin text-blue-500" />
      </div>
    );
  }

  if (!user) {
    return (
      <div className="h-screen bg-gray-900 flex flex-col">
        <div className="bg-gray-800 p-4 flex items-center justify-between">
          <button onClick={() => router.push('/chat')} className="text-blue-400 hover:text-blue-300 flex items-center">
            <IconArrowLeft size={20} className="mr-2" />
            Back
          </button>
          <h1 className="text-xl text-gray-100 font-header">Consultations</h1>
          <div></div>
        </div>
        <EmptyState title="Access Denied" message="Please sign in to view consultations." />
      </div>
    );
  }

  return (
    <div className="h-screen bg-gray-900 flex flex-col">
      {/* Header */}
      <div className="bg-gray-800 p-4 flex items-center justify-between">
        <button onClick={() => router.push('/chat')} className="text-blue-400 hover:text-blue-300 flex items-center">
          <IconArrowLeft size={20} className="mr-2" />
          Back
        </button>
        <h1 className="text-xl text-gray-100 font-header">My Consultations</h1>
        <button onClick={() => router.push('/book-consultation')} className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg flex items-center">
          <IconPlus size={18} className="mr-2" />
          Book New
        </button>
      </div>

      <div className="flex-1 flex gap-4 p-4 overflow-hidden">
        {/* Consultation List */}
        <div className="w-1/3 bg-gray-800 rounded-xl flex flex-col">
          <div className="p-4 border-b border-gray-700">
            <div className="relative">
              <input
                type="text"
                placeholder="Search consultations..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full p-3 pl-10 rounded-lg border border-gray-600 bg-gray-700 text-gray-200 placeholder-gray-500 focus:ring-2 focus:ring-blue-500"
              />
              <IconSearch className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-500" />
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-4">
            {isLoading ? (
              <div className="flex items-center justify-center h-full">
                <IconLoader size={32} className="animate-spin text-blue-500" />
              </div>
            ) : filteredChats.length === 0 ? (
              <EmptyState title="No Consultations" message="Your consultations will appear here." />
            ) : (
              filteredChats.map(chat => (
                <ConsultationItem
                  key={chat.id}
                  chat={chat}
                  isSelected={selectedChat?.id === chat.id}
                  onSelect={() => setSelectedChat(chat)}
                />
              ))
            )}
          </div>
        </div>

        {/* Consultation Detail */}
        <div className="flex-1 bg-gray-800 rounded-xl flex flex-col">
          {!selectedChat ? (
            <EmptyState 
              title="No Consultation Selected" 
              message="Select a consultation to view details."
              actionText="Book New Consultation"
              onAction={() => router.push('/book-consultation')}
            />
          ) : (
            <>
              <div className="p-4 border-b border-gray-700">
                <h2 className="text-lg text-gray-100 font-header">{selectedChat.title || 'Untitled'}</h2>
                <p className="text-xs text-gray-400">Created: {new Date(selectedChat.createdAt).toLocaleDateString()}</p>
              </div>

              <div className="flex-1 p-4 overflow-y-auto">
                {selectedChat.messages.map((msg, i) => (
                  <div key={i} className={`mb-4 flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                    <div className={`max-w-lg p-3 rounded-xl text-sm ${
                      msg.sender === 'user' ? 'bg-blue-600 text-white' : 'bg-gray-700 text-gray-200'
                    }`}>
                      {msg.text}
                      {msg.timestamp && (
                        <div className="text-xs mt-1 opacity-70">
                          {new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>

              <div className="p-4 border-t border-gray-700 grid grid-cols-2 gap-3">
                <button
                  onClick={() => handleAction('generateSOAP', setIsGeneratingSOAP, setCurrentSOAP)}
                  disabled={isGeneratingSOAP}
                  className="flex items-center justify-center bg-blue-500 hover:bg-blue-600 text-white py-2 px-4 rounded-lg disabled:opacity-50"
                >
                  <IconFileText size={18} className="mr-2" />
                  {isGeneratingSOAP ? 'Generating...' : 'Generate SOAP'}
                </button>
                
                <button
                  onClick={() => handleAction('referToDoctor', setIsCreatingReferral, setCurrentReferral)}
                  disabled={isCreatingReferral}
                  className="flex items-center justify-center bg-teal-500 hover:bg-teal-600 text-white py-2 px-4 rounded-lg disabled:opacity-50"
                >
                  <IconUsers size={18} className="mr-2" />
                  {isCreatingReferral ? 'Creating...' : 'Create Referral'}
                </button>
              </div>
            </>
          )}
        </div>
      </div>

      {/* SOAP Modal */}
      <Modal
        isOpen={!!currentSOAP}
        onClose={() => setCurrentSOAP(null)}
        title="SOAP Note"
        actions={
          currentSOAP && (
            <>
              <button 
                onClick={() => navigator.clipboard.writeText(`Subjective: ${currentSOAP.subjective}\nObjective: ${currentSOAP.objective}\nAssessment: ${currentSOAP.assessment}\nPlan: ${currentSOAP.plan.join(', ')}`)}
                className="px-5 py-2 bg-gray-700 hover:bg-gray-600 text-gray-200 rounded-lg"
              >
                Copy
              </button>
              <button 
                onClick={() => downloadText(`Subjective: ${currentSOAP.subjective}\nObjective: ${currentSOAP.objective}\nAssessment: ${currentSOAP.assessment}\nPlan: ${currentSOAP.plan.join(', ')}`, 'soap-note.txt')}
                className="px-5 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg"
              >
                Download
              </button>
            </>
          )
        }
      >
        {currentSOAP && (
          <div className="space-y-4">
            {['Subjective', 'Objective', 'Assessment', 'Plan'].map(section => (
              <div key={section}>
                <h3 className="text-blue-400 mb-2 font-header">{section}</h3>
                <div className="bg-gray-700 p-3 rounded-lg text-gray-300">
                  {section === 'Plan' 
                    ? currentSOAP.plan.map((item: string, i: number) => <div key={i}>• {item}</div>)
                    : ((val) => val instanceof Date ? val.toLocaleString() : (typeof val === 'string' ? val : null))(currentSOAP[section.toLowerCase() as keyof SOAPNote]) || 'N/A'
                  }
                </div>
              </div>
            ))}
          </div>
        )}
      </Modal>

      {/* Referral Modal */}
      <Modal
        isOpen={!!currentReferral}
        onClose={() => setCurrentReferral(null)}
        title="Referral Details"
        actions={
          currentReferral && (
            <>
              <button 
                onClick={() => navigator.clipboard.writeText(`Referral To: ${currentReferral.referralTo}\nReason: ${currentReferral.reason}\nSymptoms: ${currentReferral.symptoms.join(', ')}`)}
                className="px-5 py-2 bg-gray-700 hover:bg-gray-600 text-gray-200 rounded-lg"
              >
                Copy
              </button>
              <button 
                onClick={() => downloadText(`Referral To: ${currentReferral.referralTo}\nReason: ${currentReferral.reason}\nSymptoms: ${currentReferral.symptoms.join(', ')}`, 'referral.txt')}
                className="px-5 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg"
              >
                Download
              </button>
            </>
          )
        }
      >
        {currentReferral && (
          <div className="space-y-4">
            <div>
              <h3 className="text-blue-400 mb-2 font-header">Referral To</h3>
              <div className="bg-gray-700 p-3 rounded-lg text-gray-300">{currentReferral.referralTo}</div>
            </div>
            <div>
              <h3 className="text-blue-400 mb-2 font-header">Reason</h3>
              <div className="bg-gray-700 p-3 rounded-lg text-gray-300">{currentReferral.reason}</div>
            </div>
            <div>
              <h3 className="text-blue-400 mb-2 font-header">Symptoms</h3>
              <div className="bg-gray-700 p-3 rounded-lg text-gray-300">
                {currentReferral.symptoms.map((symptom, i) => <div key={i}>• {symptom}</div>)}
              </div>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}
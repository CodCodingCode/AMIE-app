'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '../chat/Auth';
import { chatService, Chat, SOAPNote, Referral } from '../chat/chatService';

// Ultra-simple components
import UltraSimpleHeader from './ConsultationHeader';
import UltraSimpleList from './ConsultationList';
import UltraSimpleDetail from './ConsultationDetail';
import UltraSimpleSOAPModal from './SOAPNoteModal';
import UltraSimpleReferralModal from './ReferralModal';

export default function UltraSimpleConsultationsPage() {
  const router = useRouter();
  const { user, loading: authLoading } = useAuth();
  
  const [allChats, setAllChats] = useState<Chat[]>([]);
  const [filteredChats, setFilteredChats] = useState<Chat[]>([]);
  const [isLoadingChats, setIsLoadingChats] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedChat, setSelectedChat] = useState<Chat | null>(null);
  
  const [isGeneratingSOAP, setIsGeneratingSOAP] = useState(false);
  const [isCreatingReferral, setIsCreatingReferral] = useState(false);
  
  const [showSOAPModal, setShowSOAPModal] = useState(false);
  const [showReferralModal, setShowReferralModal] = useState(false);
  
  const [currentSOAP, setCurrentSOAP] = useState<SOAPNote | null>(null);
  const [currentReferral, setCurrentReferral] = useState<Referral | null>(null);

  const loadChats = useCallback(async () => {
    if (user) {
      try {
        setIsLoadingChats(true);
        const userChats = await chatService.getUserChats(user);
        const nonEmptyChats = userChats.filter(chat => chat.messages && chat.messages.length > 0);
        setAllChats(nonEmptyChats);
        setFilteredChats(nonEmptyChats);
        if (nonEmptyChats.length > 0 && (!selectedChat || !nonEmptyChats.find(c => c.id === selectedChat.id))) {
          setSelectedChat(nonEmptyChats[0]);
        }
      } catch (error) {
        console.error('Error loading chats:', error);
        setAllChats([]);
        setFilteredChats([]);
      } finally {
        setIsLoadingChats(false);
      }
    } else {
      setAllChats([]);
      setFilteredChats([]);
      setSelectedChat(null);
      setIsLoadingChats(false);
    }
  }, [user, selectedChat]);

  useEffect(() => {
    if (!authLoading) {
      loadChats();
    }
  }, [user, authLoading, loadChats]);

  useEffect(() => {
    const filtered = searchTerm
      ? allChats.filter(chat =>
          chat.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
          (chat.metadata?.category && chat.metadata.category.toLowerCase().includes(searchTerm.toLowerCase())) ||
          (chat.metadata?.tags && chat.metadata.tags.some(tag => tag.toLowerCase().includes(searchTerm.toLowerCase())))
        )
      : allChats;
    setFilteredChats(filtered);
    if (selectedChat && !filtered.find(c => c.id === selectedChat.id)) {
      setSelectedChat(filtered.length > 0 ? filtered[0] : null);
    } else if (!selectedChat && filtered.length > 0) {
      setSelectedChat(filtered[0]);
    }
  }, [allChats, searchTerm, selectedChat]);

  const handleGenerateSOAP = async () => {
    if (!selectedChat) return;
    
    setIsGeneratingSOAP(true);
    try {
      const response = await fetch('/api/consultations', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          action: 'generateSOAP', 
          chatData: selectedChat 
        })
      });
      
      if (response.ok) {
        const result = await response.json();
        if (result.soapNote) {
          setCurrentSOAP(result.soapNote);
          setShowSOAPModal(true);
        } else {
          throw new Error(result.error || 'SOAP note data not found in response');
        }
      } else {
        const errorData = await response.json();
        throw new Error(errorData.error || `Failed to generate SOAP note (${response.status})`);
      }
    } catch (error: any) {
      console.error('Error generating SOAP note:', error);
      alert(`Error: ${error.message || 'Failed to generate SOAP note'}`);
    } finally {
      setIsGeneratingSOAP(false);
    }
  };

  const handleCreateReferral = async () => {
    if (!selectedChat || !user) return;
    
    setIsCreatingReferral(true);
    try {
      const response = await fetch('/api/consultations', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          action: 'referToDoctor', 
          chatData: selectedChat,
        })
      });
      
      if (response.ok) {
        const result = await response.json();
        if (result.referral) {
          setCurrentReferral(result.referral);
          setShowReferralModal(true);
        } else {
          throw new Error(result.error || 'Referral data not found in response');
        }
      } else {
        const errorData = await response.json();
        throw new Error(errorData.error || `Failed to create referral (${response.status})`);
      }
    } catch (error: any) {
      console.error('Error creating referral:', error);
      alert(`Error: ${error.message || 'Failed to create referral'}`);
    } finally {
      setIsCreatingReferral(false);
    }
  };

  const handleBookConsultation = async () => {
    try {
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
      window.location.href = session.url;
    } catch (err) {
      console.error('Error creating checkout session:', err);
      alert('Unable to start payment process. Please try again.');
    }
  };

  const formatDate = (date: Date): string => {
    const now = new Date();
    const diffInDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24));
    
    if (diffInDays === 0) return 'Today';
    if (diffInDays === 1) return 'Yesterday';
    if (diffInDays < 7) return `${diffInDays}d ago`;
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  const getPreviewText = (chat: Chat): string => {
    const firstUserMessage = chat.messages.find(msg => msg.sender === 'user');
    if (!firstUserMessage || !firstUserMessage.text) return 'No messages yet';
    return firstUserMessage.text.slice(0, 80) + (firstUserMessage.text.length > 80 ? '...' : '');
  };

  if (authLoading) {
    return (
      <div className="h-screen bg-smokyBlack flex items-center justify-center">
        <div className="text-white text-lg">Loading...</div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="h-screen bg-beige flex flex-col">
        <UltraSimpleHeader onBack={() => router.push('/chat')} onBook={handleBookConsultation} />
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <div className="text-dukeBlue text-xl mb-4">Please sign in</div>
            <button 
              onClick={() => router.push('/chat')}
              className="bg-dukeBlue text-white px-6 py-2 text-sm"
            >
              Go to Chat
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen bg-smokyBlack flex flex-col p-6">
      <UltraSimpleHeader onBack={() => router.push('/chat')} onBook={handleBookConsultation} />
      
      <div className="flex-1 flex gap-6 mt-6">
        {isLoadingChats ? (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-white text-lg">Loading consultations...</div>
          </div>
        ) : (
          <>
            <UltraSimpleList 
              chats={filteredChats}
              selectedChat={selectedChat}
              onSelectChat={setSelectedChat}
              searchTerm={searchTerm}
              onSearchTermChange={setSearchTerm}
              formatDate={formatDate}
              getPreviewText={getPreviewText}
            />
            <UltraSimpleDetail 
              selectedChat={selectedChat}
              onGenerateSOAP={handleGenerateSOAP}
              onCreateReferral={handleCreateReferral}
              isGeneratingSOAP={isGeneratingSOAP}
              isCreatingReferral={isCreatingReferral}
              onBookConsultation={handleBookConsultation}
            />
          </>
        )}
      </div>

      <UltraSimpleSOAPModal 
        isOpen={showSOAPModal}
        onClose={() => setShowSOAPModal(false)}
        soapNote={currentSOAP}
      />
      
      <UltraSimpleReferralModal 
        isOpen={showReferralModal}
        onClose={() => setShowReferralModal(false)}
        referral={currentReferral}
      />
    </div>
  );
}
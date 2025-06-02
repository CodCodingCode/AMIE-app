'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '../chat/Auth';
import { chatService, Chat, SOAPNote, Referral } from '../chat/chatService';
import {
  IconNotes,
  IconCreditCard
} from '@tabler/icons-react';

// Import new components
import ConsultationHeader from './ConsultationHeader';
import ConsultationList from './ConsultationList';
import ConsultationDetail from './ConsultationDetail';
import SOAPNoteModal from './SOAPNoteModal';
import ReferralModal from './ReferralModal';
import LoadingSpinner from './LoadingSpinner';
import EmptyState from './EmptyState'; // General empty state for auth

export default function ConsultationsPage() {
  const router = useRouter();
  const { user, loading: authLoading } = useAuth();
  
  const [allChats, setAllChats] = useState<Chat[]>([]); // Stores all fetched chats
  const [filteredChats, setFilteredChats] = useState<Chat[]>([]); // Chats after search filter
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
          // TODO: Consider saving SOAP note via chatService & updating metadata if API doesn't do it
          // if (user && selectedChat.id) {
          //   await chatService.saveSOAPNote({ ...result.soapNote, chatId: selectedChat.id, generatedBy: user.uid });
          //   await chatService.updateConsultationMetadata(selectedChat.id, { soapGenerated: true });
          //   loadChats(); // Reload to reflect potential metadata changes
          // }
        } else {
            throw new Error (result.error || 'SOAP note data not found in response');
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
    if (!selectedChat || !user) return; // Ensure user is available for patientId if needed
    
    setIsCreatingReferral(true);
    try {
      const response = await fetch('/api/consultations', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          action: 'referToDoctor', 
          chatData: selectedChat,
          // Assuming patientId might come from user or selectedChat.metadata if available
          // patientId: user.uid, // Example: or selectedChat.metadata.patientId
        })
      });
      
      if (response.ok) {
        const result = await response.json();
         if (result.referral) {
        setCurrentReferral(result.referral);
        setShowReferralModal(true);
            // TODO: Consider saving referral via chatService & updating metadata if API doesn't do it
            // if (selectedChat.id) {
            //   await chatService.createReferral({ ...result.referral, chatId: selectedChat.id, patientId: result.referral.patientId || user.uid });
            //   loadChats();
            // }
         } else {
            throw new Error (result.error || 'Referral data not found in response');
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

  // Utility functions passed to child components
  const formatDateForListItem = (date: Date): string => {
    const now = new Date();
    const diffInDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24));
    
    if (diffInDays === 0) return 'Today';
    if (diffInDays === 1) return 'Yesterday';
    if (diffInDays < 7) return `${diffInDays} days ago`;
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  const getPreviewTextForListItem = (chat: Chat): string => {
    const firstUserMessage = chat.messages.find(msg => msg.sender === 'user');
    if (!firstUserMessage || !firstUserMessage.text) return chat.metadata?.category || 'No messages yet';
    return firstUserMessage.text.slice(0, 100) + (firstUserMessage.text.length > 100 ? '...' : '');
  };

  if (authLoading) {
    return (
      <div className="min-h-screen bg-neutral-900 text-white flex flex-col">
        <ConsultationHeader title="Medical Consultations" onNewConsultationClick={() => router.push('/chat')} />
        <div className="flex-grow flex items-center justify-center">
            <LoadingSpinner message="Authenticating..." />
        </div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="min-h-screen bg-neutral-900 text-white flex flex-col">
        <ConsultationHeader title="Medical Consultations" onNewConsultationClick={() => router.push('/chat')} />
         <div className="flex-grow">
            <EmptyState 
                icon={IconNotes}
                title="Access Denied"
                message="Please log in to view your consultations."
                actionButton={<button onClick={() => router.push('/chat')} className="mt-4 px-4 py-2 bg-dukeBlue text-white rounded-md hover:bg-dukeBlue/80">Go to Login/Chat</button>}
            />
        </div>
      </div>
    );
  }

  // Main content when user is logged in
  return (
    <div className="min-h-screen bg-neutral-900 text-white flex flex-col relative">
      <ConsultationHeader title="Medical Consultations" onNewConsultationClick={() => router.push('/chat')} />

      <main className="max-w-full mx-auto p-4 sm:p-6 flex-grow w-full">
        {isLoadingChats ? (
          <div className="flex items-center justify-center h-[calc(100vh-200px)]">
            <LoadingSpinner message="Loading consultations..." />
          </div>
        ) : (
          <div className="grid grid-cols-12 gap-6 h-[calc(100vh-160px)] sm:h-[calc(100vh-180px)]">
            <ConsultationList 
              chats={filteredChats}
              selectedChat={selectedChat}
              onSelectChat={setSelectedChat}
              searchTerm={searchTerm}
              onSearchTermChange={setSearchTerm}
              formatDate={formatDateForListItem}
              getPreviewText={getPreviewTextForListItem}
            />
            <ConsultationDetail 
              selectedChat={selectedChat}
              onGenerateSOAP={handleGenerateSOAP}
              onCreateReferral={handleCreateReferral}
              isGeneratingSOAP={isGeneratingSOAP}
              isCreatingReferral={isCreatingReferral}
            />
          </div>
        )}
      </main>

      {/* Floating Action Button - only show when user is logged in and not loading */}
      {user && !authLoading && (
        <button
          onClick={handleBookConsultation}
          className="fixed bottom-6 right-6 bg-green-600 hover:bg-green-700 text-white px-6 py-4 rounded-full shadow-lg transition-all duration-200 flex items-center gap-2 hover:scale-105 z-50 group"
          title="Book a new consultation"
        >
          <IconCreditCard className="w-5 h-5" />
          <span className="hidden sm:inline font-medium">Book Consultation</span>
          <span className="sm:hidden font-medium">$29</span>
        </button>
      )}

      <SOAPNoteModal 
        isOpen={showSOAPModal}
        onClose={() => setShowSOAPModal(false)}
        soapNote={currentSOAP}
        // Pass consultation title if needed, e.g., from selectedChat
        // consultationTitle={selectedChat?.title}
      />
      <ReferralModal 
        isOpen={showReferralModal}
        onClose={() => setShowReferralModal(false)}
        referral={currentReferral}
        // Pass consultation title if needed
        // consultationTitle={selectedChat?.title}
      />
    </div>
  );
}
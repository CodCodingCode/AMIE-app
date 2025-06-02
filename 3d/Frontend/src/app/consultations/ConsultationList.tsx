'use client';

import React from 'react';
import { Chat } from '../chat/chatService';
import ConsultationListItem from './ConsultationListItem';
import EmptyState from './EmptyState';
import { IconSearch } from '@tabler/icons-react';

interface ConsultationListProps {
  chats: Chat[];
  selectedChat: Chat | null;
  onSelectChat: (chat: Chat) => void;
  searchTerm: string;
  onSearchTermChange: (term: string) => void;
  formatDate: (date: Date) => string;
  getPreviewText: (chat: Chat) => string;
}

const ConsultationList: React.FC<ConsultationListProps> = ({ 
  chats, 
  selectedChat, 
  onSelectChat,
  searchTerm,
  onSearchTermChange,
  formatDate,
  getPreviewText
}) => {
  return (
    <div className="col-span-12 md:col-span-5 lg:col-span-4 xl:col-span-3 bg-neutral-800 rounded-xl border border-neutral-700 flex flex-col h-full">
      {/* Search */}
      <div className="p-4 border-b border-neutral-700">
        <div className="relative">
          <IconSearch className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search consultations..."
            value={searchTerm}
            onChange={(e) => onSearchTermChange(e.target.value)}
            className="w-full pl-10 pr-4 py-2.5 bg-neutral-700 border border-neutral-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-dukeBlue text-sm"
          />
        </div>
      </div>

      {/* Consultations List */}
      <div className="overflow-y-auto flex-grow no-scrollbar">
        {chats.length === 0 ? (
          <EmptyState 
            title={searchTerm ? "No Matching Consultations" : "No Consultations Yet"}
            message={searchTerm ? "Try adjusting your search term." : "New consultations will appear here."}
          />
        ) : (
          chats.map(chat => (
            <ConsultationListItem 
              key={chat.id}
              chat={chat}
              isSelected={selectedChat?.id === chat.id}
              onSelect={() => onSelectChat(chat)}
              formatDate={formatDate}
              getPreviewText={getPreviewText}
            />
          ))
        )}
      </div>
    </div>
  );
};

export default ConsultationList; 
'use client';

import React from 'react';
import { Chat } from '../chat/chatService';

interface UltraSimpleListProps {
  chats: Chat[];
  selectedChat: Chat | null;
  onSelectChat: (chat: Chat) => void;
  searchTerm: string;
  onSearchTermChange: (term: string) => void;
  formatDate: (date: Date) => string;
  getPreviewText: (chat: Chat) => string;
}

const UltraSimpleList: React.FC<UltraSimpleListProps> = ({ 
  chats, 
  selectedChat, 
  onSelectChat,
  searchTerm,
  onSearchTermChange,
  formatDate,
  getPreviewText
}) => {
  return (
    <div className="w-1/3 bg-trueBlue rounded-xl overflow-hidden shadow-lg">
      {/* Search */}
      <div className="p-6">
        <input
          type="text"
          placeholder="Search..."
          value={searchTerm}
          onChange={(e) => onSearchTermChange(e.target.value)}
          className="w-full p-3 text-sm rounded-lg border border-mountbattenPink bg-white text-dukeBlue placeholder-mountbattenPink focus:outline-none focus:ring-2 focus:ring-dukeBlue"
        />
      </div>

      {/* List */}
      <div className="overflow-y-auto h-full px-3 pb-6">
        {chats.length === 0 ? (
          <div className="p-8 text-center text-dukeBlue">
            {searchTerm ? "No matches" : "No consultations"}
          </div>
        ) : (
          <div className="space-y-3">
            {chats.map(chat => (
              <div
                key={chat.id}
                onClick={() => onSelectChat(chat)}
                className={`p-4 rounded-lg cursor-pointer hover:bg-white transition-all duration-200 ${
                  selectedChat?.id === chat.id ? 'bg-white shadow-md border-l-4 border-l-dukeBlue' : 'bg-white/50'
                }`}
              >
                <div className="flex justify-between items-start mb-2">
                  <div className="text-sm font-medium text-dukeBlue truncate flex-1">
                    {chat.title || 'Untitled'}
                  </div>
                  <div className="text-xs text-mountbattenPink ml-2">
                    {formatDate(chat.updatedAt)}
                  </div>
                </div>
                <div className="text-xs text-mountbattenPink mb-2">
                  {getPreviewText(chat)}
                </div>
                <div className="text-xs text-mountbattenPink">
                  {chat.messages.length} msgs
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default UltraSimpleList;
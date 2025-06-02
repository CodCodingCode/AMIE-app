'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { Chat } from '../chat/chatService';
import { IconMessage, IconChevronRight } from '@tabler/icons-react';
import { cn } from '@/app/lib/utils';

interface ConsultationListItemProps {
  chat: Chat;
  isSelected: boolean;
  onSelect: () => void;
  formatDate: (date: Date) => string; // Passed from parent to ensure consistency
  getPreviewText: (chat: Chat) => string; // Passed from parent
}

const ConsultationListItem: React.FC<ConsultationListItemProps> = ({ 
  chat, 
  isSelected, 
  onSelect,
  formatDate,
  getPreviewText
}) => {
  return (
    <motion.div
      onClick={onSelect}
      className={cn(
        "p-4 border-b border-neutral-700 cursor-pointer hover:bg-neutral-700/70 transition-colors duration-150",
        isSelected ? "bg-dukeBlue/20 border-l-4 border-dukeBlue" : "border-l-4 border-transparent"
      )}
      whileHover={{ backgroundColor: isSelected ? 'rgba(0, 20, 137, 0.3)' : 'rgba(64, 64, 64, 0.7)' }}
      animate={{ 
        backgroundColor: isSelected ? 'rgba(0, 20, 137, 0.2)' : 'transparent',
        borderColor: isSelected ? '#001489' : 'transparent' 
      }}
    >
      <div className="flex items-center justify-between mb-1">
        <h4 className="text-sm font-semibold text-white truncate flex-1 pr-2">
          {chat.title || 'Untitled Consultation'}
        </h4>
        <span className="text-xs text-gray-400 whitespace-nowrap">
          {formatDate(chat.updatedAt)}
        </span>
      </div>
      <p className="text-xs text-gray-400 mb-2 truncate">
        {getPreviewText(chat)}
      </p>
      <div className="flex items-center justify-between text-xs">
        <div className="flex items-center text-gray-500">
          <IconMessage className="w-3.5 h-3.5 mr-1.5" />
          <span>{chat.messages.length} messages</span>
        </div>
        {isSelected && <IconChevronRight className="w-4 h-4 text-dukeBlue" />}
      </div>
    </motion.div>
  );
};

export default ConsultationListItem; 
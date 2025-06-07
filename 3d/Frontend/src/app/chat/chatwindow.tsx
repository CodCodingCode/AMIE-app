'use client';

import React, { useState, useRef, useEffect, useCallback } from 'react';
// Importing React and necessary hooks:
// - useState: for managing component state
// - useRef: for referencing DOM elements
// - useEffect: for side effects like scrolling
// - useCallback: for optimizing function performance

import { IconSend, IconTrash } from '@tabler/icons-react'; // Added IconTrash for delete functionality
import { ColourfulText } from './colourful';
import TextareaAutosize from 'react-textarea-autosize';
import { motion } from 'framer-motion';
import { useAuth, AuthButton } from './Auth';
import { chatService, ChatMessage as ServiceChatMessage } from './chatService'; // Renamed to avoid conflict

// Defining TypeScript types for our messages
type MessageSender = 'user' | 'assistant'; // Message can be from user or assistant
type Message = { text: string; sender: MessageSender }; // A message has text and a sender
// API message format
type ApiMessage = {
  role: 'user' | 'assistant' | 'system';
  content: string;
};

export default function ChatWindow() {
  const { user, loading: authLoading } = useAuth();
  
  const [chatState, setChatState] = useState<{
    messages: Message[];
    input: string;
    isTyping: boolean;
    partialResponse: string;
    inputHeight: number;
    isProcessing: boolean; // For sending a message
    isLoadingNewChat: boolean; // For initial new chat creation on load
    isChatLoading: boolean;    // For loading an existing chat from sidebar
    currentChatId: string | null;
    isDeleteDialogOpen: boolean;
    isDeleting: boolean;
  }>({
    messages: [],
    input: '',
    isTyping: false,
    partialResponse: '',
    inputHeight: 56,
    isProcessing: false,
    isLoadingNewChat: false, // Don't auto-create, wait for user action
    isChatLoading: false,
    currentChatId: null,
    isDeleteDialogOpen: false,
    isDeleting: false,
  });

  // Creating a reference to the bottom of our messages container
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const chatContainerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  
  // Destructuring our state for easier access
  const { 
    messages, 
    input, 
    isTyping, 
    partialResponse, 
    inputHeight, 
    isProcessing, 
    isLoadingNewChat, 
    isChatLoading, 
    currentChatId, 
    isDeleteDialogOpen,
    isDeleting
  } = chatState;

  // Function to create a new chat
  const createNewChat = useCallback(async () => {
    setChatState(prev => ({ ...prev, isLoadingNewChat: true }));
    let newChatIdFromService: string | null = null;

    if (!user) {
      // For guest users, just reset local state for a new chat
      setChatState(prev => ({
        ...prev,
        messages: [],
        currentChatId: null,
        isLoadingNewChat: false,
      }));
      if (typeof window !== 'undefined') window.dispatchEvent(new CustomEvent('refreshChatList'));
      return null;
    }
    
    try {
      newChatIdFromService = await chatService.createNewChat(user); // No initial messages by default now
      setChatState(prev => ({
        ...prev,
        messages: [],
        currentChatId: newChatIdFromService,
        isLoadingNewChat: false,
      }));
      if (typeof window !== 'undefined') window.dispatchEvent(new CustomEvent('refreshChatList'));
      return newChatIdFromService;
    } catch (error) {
      console.error('Error creating new chat:', error);
      setChatState(prev => ({ ...prev, isLoadingNewChat: false }));
      return null;
    }
  }, [user]);

  // Removed auto-creation of new chat on page load - only create when explicitly requested

  // Notify sidebar of message count changes
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const event = new CustomEvent('messageCountUpdate', { detail: { count: messages.length } });
      window.dispatchEvent(event);
    }
  }, [messages.length]);

  // Auto-scroll effect - improved to handle first message
  useEffect(() => {
    if (messagesEndRef.current && !isChatLoading) {
      // For the first message, scroll to top first, then to bottom
      if (messages.length === 1) {
        // Scroll to top first to ensure first message is visible
        if (chatContainerRef.current) {
          const scrollContainer = chatContainerRef.current.querySelector('.chat-container');
          if (scrollContainer) {
            scrollContainer.scrollTop = 0;
            // Then smooth scroll to show the message
            setTimeout(() => {
              messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
            }, 50);
          }
        }
      } else {
        messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
      }
    }
  }, [messages, isTyping, partialResponse, isChatLoading]);

  // Handle changes to the input textarea
  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setChatState(prev => ({ ...prev, input: e.target.value }));
  }, []);

  // Handle sending a message and receiving a response
  const handleSendMessage = useCallback(async () => {
    if (!input.trim() || isProcessing) return;

    const userMessage: Message = { text: input.trim(), sender: 'user' };
    let activeChatId = currentChatId;

    setChatState(prev => ({
      ...prev,
      messages: [...prev.messages, userMessage],
      input: '',
      isTyping: true,
      partialResponse: '',
      isProcessing: true
    }));
    
    try {
      if (user) {
        if (!activeChatId) {
          const newId = await createNewChat(); // This will also set currentChatId in state
          if (newId) activeChatId = newId;
          else {
            setChatState(prev => ({ ...prev, isTyping: false, isProcessing: false }));
            console.error("Failed to create new chat before sending message.");
            return; // Early exit if chat creation failed
          }
        }
        await chatService.addMessageToChat(activeChatId!, userMessage as Omit<ServiceChatMessage, 'timestamp'>);
        if (typeof window !== 'undefined') window.dispatchEvent(new CustomEvent('refreshChatList'));
      }

      const historyForApi: ApiMessage[] = [...messages, userMessage].map(msg => ({
        role: msg.sender,
        content: msg.text
      }));

      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMessage.text, history: historyForApi }),
      });

      if (!response.ok || !response.body) {
        throw new Error(`Server error: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let accumulatedText = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) {
          const assistantMessage: Message = { text: accumulatedText, sender: 'assistant' };
          if (user && activeChatId) {
            await chatService.addMessageToChat(activeChatId, assistantMessage as Omit<ServiceChatMessage, 'timestamp'>);
            if (typeof window !== 'undefined') window.dispatchEvent(new CustomEvent('refreshChatList'));
          }
          setChatState(prev => ({
            ...prev,
            messages: [...prev.messages, assistantMessage],
            isTyping: false,
            partialResponse: '',
            isProcessing: false
          }));
          break;
        }
        const chunkText = decoder.decode(value, { stream: true });
        accumulatedText += chunkText;
        setChatState(prev => ({ ...prev, partialResponse: accumulatedText }));
      }
    } catch (error) {
      console.error('Error sending message:', error);
      setChatState(prev => ({ ...prev, isTyping: false, isProcessing: false }));
    }
  }, [input, messages, isProcessing, user, currentChatId, createNewChat]);

  // Function to load a specific chat
  const loadChat = useCallback(async (chatId: string) => {
    if (!user) return; // Should not happen if UI hides load options for guests
    setChatState(prev => ({ ...prev, isChatLoading: true, messages: [], currentChatId: null })); // Clear current before loading
    try {
      const chat = await chatService.getChat(chatId);
      if (chat) {
        setChatState(prev => ({
          ...prev,
          messages: chat.messages.map(msg => ({ text: msg.text, sender: msg.sender as MessageSender })),
          currentChatId: chatId,
          isChatLoading: false,
          isLoadingNewChat: false, // Loaded an existing chat
        }));
      } else {
        console.error("Failed to load chat, or chat does not exist.");
        setChatState(prev => ({ ...prev, isChatLoading: false, isLoadingNewChat: true })); // Fallback to new chat logic
      }
    } catch (error) {
      console.error('Error loading chat:', error);
      setChatState(prev => ({ ...prev, isChatLoading: false, isLoadingNewChat: true })); // Fallback
    }
  }, [user]);

  // Make loadChat and createNewChat available globally
  useEffect(() => {
    if (typeof window !== 'undefined') {
      (window as any).loadChat = loadChat;
      (window as any).createNewChat = createNewChat; // No EHR summary to pass now
    }
    // Cleanup global assignments
    return () => {
      if (typeof window !== 'undefined') {
        delete (window as any).loadChat;
        delete (window as any).createNewChat;
        delete (window as any).deleteCurrentChat;
      }
    };
  }, [loadChat, createNewChat, currentChatId, user]); // Added user here

  return (
    <div className="flex-1 flex flex-col h-screen bg-gray-50 dark:bg-neutral-950">
      <div
        ref={chatContainerRef}
        className="flex-1 flex flex-col max-w-4xl mx-auto w-full px-4 relative overflow-hidden"
      >
        {/* Display sign-in prompt for unauthenticated users */}
        {!user && !authLoading && (
          <div className="bg-blue-50/80 dark:bg-blue-900/20 backdrop-blur-sm rounded-2xl p-4 mb-4 mt-6 flex items-center justify-between border border-blue-200/50 dark:border-blue-800/50">
            <p className="text-sm text-blue-800 dark:text-blue-200">
              Sign in to save your chat history
            </p>
            <div className="flex-shrink-0">
              <AuthButton />
            </div>
          </div>
        )}
        
        <div className="flex-1 overflow-y-auto pb-40 pt-6 chat-container" style={{ scrollBehavior: 'smooth' }}>
          {(isLoadingNewChat || isChatLoading) ? (
            <div className="flex items-center justify-center h-full">
              <div className="flex items-center space-x-3 bg-white/80 dark:bg-neutral-800/80 backdrop-blur-sm rounded-full px-6 py-4 shadow-lg">
                <div className="flex space-x-1">
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0s' }}></div>
                  <div className="w-2 h-2 bg-purple-500 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                  <div className="w-2 h-2 bg-pink-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                </div>
                <p className="text-gray-700 dark:text-gray-300 text-sm">
                  {(isLoadingNewChat && !currentChatId) ? "Starting new chat..." : "Loading chat..."}
                </p>
              </div>
            </div>
          ) : (
            <>
              {/* Welcome screen - only show when no messages and not processing */}
              {messages.length === 0 && !isTyping && !partialResponse && !isProcessing && (
                <div className="text-center absolute top-1/3 left-0 right-0 z-0 pointer-events-none">
                  <div className="space-y-4">
                    <h1 className="text-gray-600 dark:text-gray-400 text-4xl md:text-5xl tracking-wide font-header">
                      Welcome to the
                    </h1>
                    <div className="transform scale-110">
                      <ColourfulText text="Bluebox" />
                    </div>
                    <p className="text-gray-500 dark:text-gray-500 text-lg mt-6">
                      Your AI health companion
                    </p>
                  </div>
                </div>
              )}

              {/* Messages container with proper spacing */}
              {(messages.length > 0 || isTyping || partialResponse || isProcessing) && (
                <div className="min-h-full">
                  {messages.map((message, index) => (
                    <div
                      key={index}
                      className={`message mb-8 animate-fadeIn ${
                        message.sender === 'user' ? 'flex justify-end' : ''
                      }`}
                    >
                      {message.sender === 'user' ? (
                        // User message - Gemini-style bubble
                        <div className="max-w-[70%] bg-gradient-to-r from-blue-500 to-purple-600 text-white p-4 rounded-3xl rounded-br-lg shadow-md backdrop-filter backdrop-blur-sm border border-white/10">
                          <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.text}</p>
                        </div>
                      ) : (
                        // Assistant message - clean, minimal style like Gemini
                        <div className="max-w-full">
                          <div className="bg-white/60 dark:bg-neutral-800/60 backdrop-blur-sm rounded-3xl p-6 shadow-sm border border-gray-200/50 dark:border-neutral-700/50">
                            <p className="text-gray-800 dark:text-gray-200 text-base leading-relaxed whitespace-pre-wrap">
                              {message.text}
                            </p>
                          </div>
                        </div>
                      )}
                    </div>
                  ))}

                  {/* Partial response with improved styling */}
                  {partialResponse && (
                    <div className="message mb-8 animate-fadeIn">
                      <div className="bg-white/60 dark:bg-neutral-800/60 backdrop-blur-sm rounded-3xl p-6 shadow-sm border border-gray-200/50 dark:border-neutral-700/50">
                        <p className="text-gray-800 dark:text-gray-200 text-base leading-relaxed whitespace-pre-wrap">
                          {partialResponse}
                        </p>
                        <div className="flex items-center mt-3 space-x-1">
                          <div className="w-1 h-1 bg-blue-500 rounded-full animate-pulse"></div>
                          <div className="w-1 h-1 bg-purple-500 rounded-full animate-pulse" style={{ animationDelay: '0.2s' }}></div>
                          <div className="w-1 h-1 bg-pink-500 rounded-full animate-pulse" style={{ animationDelay: '0.4s' }}></div>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Typing indicator with Gemini-style design */}
                  {isTyping && !partialResponse && (
                    <div className="mb-8">
                      <div className="bg-white/60 dark:bg-neutral-800/60 backdrop-blur-sm rounded-3xl p-6 shadow-sm border border-gray-200/50 dark:border-neutral-700/50">
                        <div className="flex items-center space-x-2">
                          <div className="flex space-x-1">
                            {[0, 0.2, 0.4].map((delay, i) => (
                              <div
                                key={i}
                                className="w-2 h-2 rounded-full bg-gradient-to-r from-blue-500 to-purple-600 animate-bounce"
                                style={{ animationDelay: delay ? `${delay}s` : undefined }}
                              />
                            ))}
                          </div>
                          <span className="text-gray-500 dark:text-gray-400 text-sm">Thinking...</span>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Message input area - Gemini-style design */}
        <div className="fixed bottom-0 left-0 right-0 z-10 bg-gradient-to-t from-gray-50 via-gray-50 to-transparent dark:from-neutral-950 dark:via-neutral-950 dark:to-transparent pt-8 pb-6">
          <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
            
            {/* Main input container with Gemini-style rounded design */}
            <div className="relative">
              <div className="bg-white dark:bg-neutral-800 rounded-3xl border border-gray-200 dark:border-neutral-700 shadow-lg hover:shadow-xl transition-shadow duration-200 overflow-hidden">
                
                {/* Top section with input and send button - fixed minimum height */}
                <div className="flex items-end p-2 min-h-[72px]">
                  
                  {/* Text input area */}
                  <div className="flex-1 min-h-0 flex items-end">
                    <TextareaAutosize
                      ref={inputRef}
                      value={input}
                      onChange={handleInputChange}
                      onKeyDown={e => {
                        if (e.key === 'Enter' && !e.shiftKey) {
                          e.preventDefault();
                          handleSendMessage();
                        }
                      }}
                      placeholder="What brings you in today?"
                      className="w-full py-4 px-5 bg-transparent focus:outline-none resize-none text-gray-800 dark:text-gray-200 placeholder-gray-500 dark:placeholder-gray-400 text-base leading-relaxed min-h-[24px] max-h-[200px] block"
                      minRows={1}
                      maxRows={8}
                      disabled={isProcessing || isLoadingNewChat || isChatLoading}
                    />
                  </div>
                  
                  {/* Send button */}
                  <div className="flex-shrink-0 p-2 flex items-end">
                    <button
                      onClick={handleSendMessage}
                      disabled={!input.trim() || isProcessing || isLoadingNewChat || isChatLoading}
                      className={`
                        relative overflow-hidden rounded-full p-3 transition-all duration-200 transform
                        ${(!input.trim() || isProcessing || isLoadingNewChat || isChatLoading) 
                          ? 'bg-gray-100 dark:bg-neutral-700 text-gray-400 cursor-not-allowed' 
                          : 'bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white shadow-md hover:shadow-lg hover:scale-105 active:scale-95'
                        }
                        focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50
                      `}
                    >
                      {isProcessing ? (
                        <div className="h-5 w-5 flex items-center justify-center">
                          <div className="w-4 h-4 border-2 border-gray-400 border-t-transparent rounded-full animate-spin"></div>
                        </div>
                      ) : (
                        <IconSend className="h-5 w-5" />
                      )}
                      
                      {/* Ripple effect for active button */}
                      {!(!input.trim() || isProcessing || isLoadingNewChat || isChatLoading) && (
                        <div className="absolute inset-0 rounded-full bg-white opacity-0 hover:opacity-10 transition-opacity duration-200"></div>
                      )}
                    </button>
                  </div>
                </div>
                
                {/* Bottom action bar - fixed height */}
                <div className="flex items-center justify-between px-5 pb-3 pt-1 h-[40px]">
                  <div className="flex items-center space-x-1">
                    {/* You can add attachment, voice, or other action buttons here */}
                    <button className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 rounded-full hover:bg-gray-100 dark:hover:bg-neutral-700 transition-colors">
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
                      </svg>
                    </button>
                    <button className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 rounded-full hover:bg-gray-100 dark:hover:bg-neutral-700 transition-colors">
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                      </svg>
                    </button>
                  </div>
                  
                  <div className="text-xs text-gray-400 dark:text-gray-500">
                    Press Enter to send
                  </div>
                </div>
              </div>
              
              {/* Character count or other info - positioned absolutely to not affect layout */}
              {input.length > 1000 && (
                <div className="absolute -top-6 right-2">
                  <span className="text-xs text-gray-400 dark:text-gray-500 bg-white dark:bg-neutral-800 px-2 py-1 rounded-full shadow-sm">
                    {input.length}/2000
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Delete Confirmation Dialog */}
      {isDeleteDialogOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 backdrop-blur-sm">
          <div className="bg-white dark:bg-neutral-800 rounded-2xl p-6 max-w-sm mx-4 shadow-xl border border-gray-200 dark:border-neutral-700">
            <h3 className="text-lg text-gray-900 dark:text-gray-100 mb-4 font-header">Delete Chat</h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-6">
              Are you sure you want to delete this chat? This action cannot be undone.
            </p>
            <div className="flex justify-end space-x-3">
              <button
                disabled={isDeleting}
                className="px-4 py-2 text-sm text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-neutral-700 rounded-xl hover:bg-gray-200 dark:hover:bg-neutral-600 focus:outline-none focus:ring-2 focus:ring-gray-500 transition-colors"
              >
                Cancel
              </button>
              <button
                disabled={isDeleting}
                className={`px-4 py-2 text-sm text-white bg-red-600 rounded-xl hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 transition-colors ${
                  isDeleting ? 'opacity-50 cursor-not-allowed' : ''
                }`}
              >
                {isDeleting ? 'Deleting...' : 'Delete'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* CSS Styles for animations and custom scrollbar */}
      <style jsx>{`
        .chat-container::-webkit-scrollbar {
          width: 4px;
        }

        .chat-container::-webkit-scrollbar-track {
          background: transparent;
        }

        .chat-container::-webkit-scrollbar-thumb {
          background: #d1d5db;
          border-radius: 2px;
        }

        .chat-container::-webkit-scrollbar-thumb:hover {
          background: #9ca3af;
        }

        .dark .chat-container::-webkit-scrollbar-thumb {
          background: #4b5563;
        }

        .dark .chat-container::-webkit-scrollbar-thumb:hover {
          background: #6b7280;
        }

        .animate-fadeIn {
          animation: fadeIn 0.3s ease-out;
        }

        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }

        @keyframes pulse {
          0%, 100% { opacity: 0.6; }
          50% { opacity: 1; }
        }

        .typing-indicator {
          animation: pulse 1.5s ease-in-out infinite;
        }
      `}</style>
    </div>
  );
}
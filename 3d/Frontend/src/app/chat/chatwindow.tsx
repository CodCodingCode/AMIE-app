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

  // Auto-scroll effect
  useEffect(() => {
    if (messagesEndRef.current && !isChatLoading) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isTyping, partialResponse, isChatLoading]);

  // Handle changes to the input textarea
  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setChatState(prev => ({ ...prev, input: e.target.value }));
  }, []);

  // Handle input height changes
  const handleHeightChange = useCallback((height: number) => {
    setChatState(prev => ({ ...prev, inputHeight: height }));
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

  // Function to render each message bubble
  const renderMessage = useCallback((message: Message, index: number) => (
    <div
      key={index}
      className={`message mb-6 animate-fadeIn ${
        message.sender === 'user' ? 'flex justify-end' : ''
      }`}
    >
      {message.sender === 'user' ? (
        // User message - displayed in blue bubble at top right
        <div className="max-w-xs bg-gray-800 text-white p-4 rounded-2xl rounded-tr-sm shadow-sm">
          <p className="text-sm whitespace-pre-wrap">{message.text}</p>
        </div>
      ) : (
        // Assistant message - displayed differently
        <div className="max-w-full text-gray-800 dark:text-gray-200 py-2 text-lg leading-relaxed">
          <p className="whitespace-pre-wrap">{message.text}</p>
        </div>
      )}
    </div>
  ), []);

  return (
    <div className="flex-1 flex flex-col h-screen">
      <div
        ref={chatContainerRef}
        className="flex-1 flex flex-col max-w-5xl mx-auto w-full px-4 relative overflow-hidden"
      >
        {/* Display sign-in prompt for unauthenticated users */}
        {!user && !authLoading && (
          <div className="bg-blue-50 dark:bg-blue-900/30 rounded-lg p-4 mb-4 mt-4 flex items-center justify-between">
            <p className="text-sm text-blue-800 dark:text-blue-200">
              Sign in to save your chat history
            </p>
            <div className="flex-shrink-0">
              <AuthButton />
            </div>
          </div>
        )}
        
        <div className="flex-1 overflow-y-auto pb-32 pt-12">
          {(isLoadingNewChat || isChatLoading) ? (
            <div className="flex items-center justify-center h-full">
              <div className="w-4 h-4 bg-gray-400 rounded-full animate-pulse"></div>
              <p className="ml-2 text-gray-600 dark:text-gray-400 text-sm animate-pulse">
                {(isLoadingNewChat && !currentChatId) ? "Starting new chat..." : "Loading chat..."}
              </p>
            </div>
          ) : (
            <>
              {messages.map(renderMessage)}

              {messages.length === 0 && !isTyping && !partialResponse && (
                <div className="text-center fixed top-1/3 left-0 right-0 z-0 pointer-events-none">
                  <h1 className="font-bold text-gray-800 dark:text-gray-200" style={{ fontSize: '5em' }}> Welcome to the </h1>
                  <ColourfulText text="Bluebox" />
                </div>
              )}

              {partialResponse && (
                <div className="message mb-6 animate-fadeIn">
                  <div className="max-w-full text-gray-800 dark:text-gray-200 py-2 text-lg leading-relaxed">
                    <p className="whitespace-pre-wrap">{partialResponse}</p>
                  </div>
                </div>
              )}

              {isTyping && !partialResponse && (
                <div className="mb-6">
                  <div className="flex space-x-2 py-2">
                    {[0, 0.2, 0.4].map((delay, i) => (
                      <div
                        key={i}
                        className="w-2 h-2 rounded-full bg-gray-400 animate-bounce"
                        style={{ animationDelay: delay ? `${delay}s` : undefined }}
                      />
                    ))}
                  </div>
                </div>
              )}
            </>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Message input area - fixed at bottom of screen - REVAMPED */}
        <div className="fixed bottom-0 left-0 right-0 z-10 bg-gray-100 dark:bg-neutral-900"> {/* Solid background for the entire fixed bar */}
          <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8"> {/* Responsive padding */}
            
            {/* Input container */}
            <div className="bg-white dark:bg-neutral-800 rounded-xl border border-gray-300 dark:border-neutral-600 p-1.5 sm:p-2 flex items-end mb-3 sm:mb-4 shadow-lg">
                <TextareaAutosize
                  ref={inputRef}
                  value={input}
                  onChange={handleInputChange}
                  onHeightChange={handleHeightChange}
                  onKeyDown={e => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      handleSendMessage();
                    }
                  }}
                  placeholder="What brings you in today?"
                  className="py-2.5 px-3 mr-2 bg-transparent focus:outline-none resize-none text-gray-800 dark:text-gray-200 flex-1 min-h-[96px] max-h-[200px] placeholder-gray-500 dark:placeholder-gray-400 text-base"
                  minRows={1}
                  maxRows={8}
                  disabled={isProcessing || isLoadingNewChat || isChatLoading}
                />
              
              <div className="flex-shrink-0">
                <button
                  onClick={handleSendMessage}
                  disabled={!input.trim() || isProcessing || isLoadingNewChat || isChatLoading}
                  className={`p-2.5 rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50 ${
                    (!input.trim() || isProcessing || isLoadingNewChat || isChatLoading) ? 'text-gray-400 bg-gray-100 dark:bg-neutral-700 cursor-not-allowed' : 'text-white bg-blue-600 hover:bg-blue-700 active:bg-blue-800'
                  }`}
                >
                  {isProcessing ? (
                    <div className="h-5 w-5 flex items-center justify-center">
                      <div className="w-3.5 h-3.5 bg-gray-400 rounded-full animate-pulse"></div>
                    </div>
                  ) : (
                    <IconSend className="h-5 w-5" />
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Delete Confirmation Dialog */}
      {isDeleteDialogOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
          <div className="bg-white rounded-lg p-6 max-w-sm mx-4 shadow-xl">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Delete Chat</h3>
            <p className="text-sm text-gray-600 mb-6">
              Are you sure you want to delete this chat? This action cannot be undone.
            </p>
            <div className="flex justify-end space-x-3">
              <button
                disabled={isDeleting}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500"
              >
                Cancel
              </button>
              <button
                disabled={isDeleting}
                className={`px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 ${
                  isDeleting ? 'opacity-50 cursor-not-allowed' : ''
                }`}
              >
                {isDeleting ? 'Deleting...' : 'Delete'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
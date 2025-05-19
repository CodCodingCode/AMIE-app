'use client';

import React, { useState, useRef, useEffect, useCallback } from 'react';
// Importing React and necessary hooks:
// - useState: for managing component state
// - useRef: for referencing DOM elements
// - useEffect: for side effects like scrolling
// - useCallback: for optimizing function performance

import { IconSend } from '@tabler/icons-react'; // Importing icons
import { ColourfulText } from './colourful';
import TextareaAutosize from 'react-textarea-autosize';
import { motion } from 'framer-motion';
import { useAuth, AuthButton } from './Auth';
import { chatService } from './chatService';

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
  
  // State management for our chat application
  const [chatState, setChatState] = useState<{
    messages: Message[];
    input: string;
    isTyping: boolean;
    partialResponse: string;
    inputHeight: number;
    isProcessing: boolean;
    isLoading: boolean;           // used for initial app load
    isChatLoading: boolean;       // NEW: used for switching between chats
    currentChatId: string | null;
  }>({
    messages: [],
    input: '',
    isTyping: false,
    partialResponse: '',
    inputHeight: 56,
    isProcessing: false,
    isLoading: false,       // for overall app
    isChatLoading: false,   // for switching chats
    currentChatId: null
  });

  // Creating a reference to the bottom of our messages container
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const chatContainerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  
  // Destructuring our state for easier access
  const { messages, input, isTyping, partialResponse, inputHeight, isProcessing, isLoading, currentChatId, isChatLoading } = chatState;

  // Load most recent chat on initial load if user is authenticated
  useEffect(() => {
    const loadMostRecentChat = async () => {
      if (!user || authLoading) return;
      
      try {
        setChatState(prev => ({ ...prev, isLoading: true }));
        // Get user's chats
        const userChats = await chatService.getUserChats(user);
        
        // If user has chats, load the most recent one
        if (userChats.length > 0) {
          const mostRecentChat = userChats[0];
          
          setChatState(prev => ({
            ...prev,
            messages: mostRecentChat.messages.map(msg => ({
              text: msg.text,
              sender: msg.sender
            })),
            currentChatId: mostRecentChat.id,
            isLoading: false
          }));
        } else {
          // No existing chats
          setChatState(prev => ({ ...prev, isLoading: false }));
        }
      } catch (error) {
        console.error('Error loading chat:', error);
        setChatState(prev => ({ ...prev, isLoading: false }));
      }
    };

    if (user && !authLoading) {
      loadMostRecentChat();
    }
  }, [user, authLoading]);

  // Notify sidebar of message count changes
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const event = new CustomEvent('messageCountUpdate', { 
        detail: { count: messages.length } 
      });
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

  // Function to create new chat
  const createNewChat = useCallback(async () => {
    // If we already have an empty chat (no messages), don't create a new one
    if (messages.length === 0) {
      return; // Already in a fresh chat, no need to create a new one
    }
    
    if (!user) {
      // For non-authenticated users, just clear the messages
      setChatState(prev => ({
        ...prev,
        messages: [],
        currentChatId: null
      }));
      return;
    }
    
    try {
      // Create a new chat in Firebase
      const newChatId = await chatService.createNewChat(user);
      
      // Update local state but don't delete existing chats
      setChatState(prev => ({
        ...prev,
        messages: [], // Clear only the messages for the new chat
        currentChatId: newChatId
      }));
      
      // Trigger chat list refresh
      if (typeof window !== 'undefined') {
        const event = new CustomEvent('refreshChatList');
        window.dispatchEvent(event);
      }
    } catch (error) {
      console.error('Error creating new chat:', error);
    }
  }, [user, messages]);

  // Handle sending a message and receiving a response
  const handleSendMessage = useCallback(async () => {
    if (!input.trim() || isProcessing) return;

    const userMessage = { text: input.trim(), sender: 'user' as const };
    
    setChatState(prev => ({
      ...prev,
      messages: [...prev.messages, userMessage],
      input: '',
      isTyping: true,
      partialResponse: '',
      inputHeight: 56,
      isProcessing: true
    }));

    try {
      let activeChatId = currentChatId;
      
      // For authenticated users
      if (user) {
        // Create new chat if we don't have one
        if (!activeChatId) {
          activeChatId = await chatService.createNewChat(user);
          setChatState(prev => ({ 
            ...prev, 
            currentChatId: activeChatId 
          }));
          
          // Refresh chat list
          if (typeof window !== 'undefined') {
            const event = new CustomEvent('refreshChatList');
            window.dispatchEvent(event);
          }
        }
        
        // Store message in Firestore
        await chatService.addMessageToChat(activeChatId, userMessage);
        
        // Refresh chat list to update chat titles
        if (typeof window !== 'undefined') {
          const event = new CustomEvent('refreshChatList');
          window.dispatchEvent(event);
        }
      }

      // Convert message history to API format
      const history: ApiMessage[] = messages.map(msg => ({
        role: msg.sender as 'user' | 'assistant',
        content: msg.text
      }));

      // Send message to our Next.js API route
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userMessage.text,
          history
        }),
      });

      if (!response.ok || !response.body) {
        throw new Error(`Server error: ${response.status}`);
      }

      // Process the stream
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let accumulatedText = '';

      while (true) {
        const { done, value } = await reader.read();
        
        if (done) {
          // Create assistant message
          const assistantMessage = { 
            text: accumulatedText, 
            sender: 'assistant' as const 
          };
          
          // Store in Firestore for authenticated users
          if (user && activeChatId) {
            await chatService.addMessageToChat(activeChatId, assistantMessage);
            
            // Add this:
            if (typeof window !== 'undefined') {
              const event = new CustomEvent('refreshChatList');
              window.dispatchEvent(event);
            }
          }
          
          // Update UI
          setChatState(prev => ({
            ...prev,
            messages: [...prev.messages, assistantMessage],
            isTyping: false,
            partialResponse: '',
            isProcessing: false
          }));
          break;
        }
        
        // Update partial response
        const chunkText = decoder.decode(value, { stream: true });
        accumulatedText += chunkText;
        
        setChatState(prev => ({
          ...prev,
          partialResponse: accumulatedText
        }));
      }
    } catch (error) {
      console.error('Error sending message:', error);
      setChatState(prev => ({
        ...prev,
        isTyping: false,
        isProcessing: false
      }));
    }
  }, [input, messages, isProcessing, user, currentChatId]);

  // Function to load a specific chat
  const loadChat = useCallback(async (chatId: string) => {
    if (!user) return;
    
    try {
      setChatState(prev => ({ ...prev, isChatLoading: true }));
      
      const chat = await chatService.getChat(chatId);
      if (chat) {
        setChatState(prev => ({
          ...prev,
          messages: chat.messages.map(msg => ({
            text: msg.text,
            sender: msg.sender
          })),
          currentChatId: chatId,
          isChatLoading: false
        }));
      } else {
        setChatState(prev => ({ ...prev, isChatLoading: false }));
      }
    } catch (error) {
      console.error('Error loading chat:', error);
      setChatState(prev => ({ ...prev, isChatLoading: false }));
    }
  }, [user]);

  // Make loadChat and createNewChat available globally
  useEffect(() => {
    if (typeof window !== 'undefined') {
      // @ts-ignore
      window.loadChat = loadChat;
      // @ts-ignore
      window.createNewChat = createNewChat;
    }
  }, [loadChat, createNewChat]);

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
        <div className="max-w-xs bg-dukeBlue text-white p-4 rounded-2xl rounded-tr-sm shadow-sm">
          <p className="text-sm whitespace-pre-wrap">{message.text}</p>
        </div>
      ) : (
        // Assistant message - displayed differently
        <div className="max-w-full text-mountbattenPink dark:text-mountbattenPink py-2 text-lg leading-relaxed">
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
          <div className="bg-trueBlue dark:bg-trueBlue rounded-lg p-4 mb-4 mt-4 flex items-center justify-between">
            <p className="text-sm text-dukeBlue dark:text-dukeBlue">
              Sign in to save your chat history
            </p>
            <div className="flex-shrink-0">
              <AuthButton />
            </div>
          </div>
        )}
        
        <div className="flex-1 overflow-y-auto pb-32 pt-12">
          {isLoading ? (
            <div className="flex items-center justify-center h-full">
              <div className="w-4 h-4 bg-mountbattenPink rounded-full animate-pulse"></div>
            </div>
          ) : isChatLoading ? (
            <div className="flex items-center justify-center h-full">
              <p className="text-mountbattenPink dark:text-mountbattenPink text-sm animate-pulse">Loading chat...</p>
            </div>
          ) : (
            <>
              {messages.map(renderMessage)}

              {messages.length === 0 && (
                <div className="text-center fixed top-1/3 left-0 right-0 z-0 pointer-events-none">
                  <h1 className="font-bold text-mountbattenPink" style={{ fontSize: '5em' }}> Welcome to the </h1>
                  <ColourfulText text="Bluebox" />
                </div>
              )}

              {partialResponse && (
                <div className="message mb-6 animate-fadeIn">
                  <div className="max-w-full text-mountbattenPink dark:text-mountbattenPink py-2 text-lg leading-relaxed">
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
                        className="w-2 h-2 rounded-full bg-mountbattenPink animate-bounce"
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
        <div className="fixed bottom-0 left-0 right-0 z-10 bg-white"> {/* Solid background for the entire fixed bar */}
          <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8"> {/* Responsive padding */}
            
            {/* Input container */}
            <div className="bg-trueBlue rounded-xl border border-mountbattenPink p-1.5 sm:p-2 flex items-end mb-3 sm:mb-4 shadow-lg">
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
                  className="py-2.5 px-3 mr-2 bg-transparent focus:outline-none resize-none text-mountbattenPink flex-1 min-h-[96px] max-h-[200px] placeholder-mountbattenPink text-base"
                  minRows={1}
                  maxRows={8}
                  disabled={isProcessing || isLoading || isChatLoading}
                />
              
              <div className="flex-shrink-0">
                <button
                  onClick={handleSendMessage}
                  disabled={!input.trim() || isProcessing || isLoading || isChatLoading}
                  className={`p-2.5 rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-dukeBlue focus:ring-opacity-50 ${
                    !input.trim() || isProcessing || isLoading || isChatLoading
                      ? 'text-mountbattenPink bg-beige cursor-not-allowed'
                      : 'text-white bg-dukeBlue hover:bg-trueBlue hover:text-dukeBlue active:bg-trueBlue'
                  }`}
                >
                  {isProcessing ? (
                    <div className="h-5 w-5 flex items-center justify-center">
                      <div className="w-3.5 h-3.5 bg-mountbattenPink rounded-full animate-pulse"></div>
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
    </div>
  );
}
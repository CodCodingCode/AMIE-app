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
import { useAuth, AuthButton } from './Auth';
import { chatService } from './chatService';
import { useEhr } from '../contexts/EhrContext'; // Import useEhr

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
  const { consumeEhrSummary } = useEhr();
  
  const [chatState, setChatState] = useState<{
    messages: Message[];
    input: string;
    isTyping: boolean;
    partialResponse: string;
    inputHeight: number;
    isProcessing: boolean;
    isLoading: boolean; 
    isChatLoading: boolean; // This might be redundant if isLoading covers new chat creation too
    currentChatId: string | null;
    initialSystemMessage: string | null;
    isDeleteDialogOpen: boolean; // State for delete confirmation dialog
    isDeleting: boolean; // State for deletion in progress
  }>({
    messages: [],
    input: '',
    isTyping: false,
    partialResponse: '',
    inputHeight: 56,
    isProcessing: false,
    isLoading: true, // Start with loading true to trigger new chat creation
    isChatLoading: false,
    currentChatId: null,
    initialSystemMessage: null,
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
    isLoading, 
    currentChatId, 
    isChatLoading, 
    initialSystemMessage,
    isDeleteDialogOpen,
    isDeleting
  } = chatState;

  // Effect to prime state for a new chat on load or user change
  useEffect(() => {
    if (authLoading) {
      return; // Wait for auth to resolve
    }
    const summaryFromContext = consumeEhrSummary();
    console.log("ChatWindow: Priming for new chat. EHR Summary from context:", summaryFromContext);
    setChatState(prev => ({
      ...prev,
      messages: [], 
      currentChatId: null, 
      initialSystemMessage: summaryFromContext, // Use summary from context, will be null if none
      isLoading: true, // Signal that a new chat setup is pending
      isChatLoading: false // Not loading an existing chat from list
    }));
  }, [user, authLoading, consumeEhrSummary]);

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

  // createNewChat function (ensure dependencies are correct, especially if it modifies `messages`)
  const createNewChat = useCallback(async (summaryForNewChat?: string) => {
    if (messages.length === 0 && !summaryForNewChat && currentChatId !== null) {
        // If already in a fresh chat (currentChatId is set, messages empty, no new summary), do nothing further to avoid loops.
        // However, the priming useEffect above will always set currentChatId to null to force this.
    }

    let newChatInitialMessages: Message[] = [];
    if (summaryForNewChat) {
      const systemText = `EHR Summary for context: ${summaryForNewChat}`;
      // Decide if this system message should be visually added or only for API
      // For now, let's assume it's added to initialMessages if chatService stores it.
      // If chatService doesn't store it, then it should only be added to historyForApi in handleSendMessage.
      // Based on current chatService, it *does* store initialMessages.
      newChatInitialMessages.push({ text: systemText, sender: 'assistant' }); // Marked as assistant for display/storage for now
      console.log("createNewChat: Preparing new chat with EHR summary.");
    }    
    
    if (!user) {
      setChatState(prev => ({
        ...prev,
        messages: newChatInitialMessages, 
        currentChatId: null, // Guest chats are local only
        initialSystemMessage: null // Consumed
      }));
      // For guest users, newChatId will be null, no backend call.
      if (typeof window !== 'undefined') window.dispatchEvent(new CustomEvent('refreshChatList')); // update sidebar if needed
      return null; // No backend ID for guest chats typically
    }
    
    try {
      // Ensure user is not null before calling service that expects User type
      const newChatIdFromService = await chatService.createNewChat(user, newChatInitialMessages);
      setChatState(prev => ({
        ...prev,
        messages: newChatInitialMessages,
        currentChatId: newChatIdFromService,
        initialSystemMessage: null // Consumed
      }));
      if (typeof window !== 'undefined') window.dispatchEvent(new CustomEvent('refreshChatList'));
      return newChatIdFromService;
    } catch (error) {
      console.error('Error creating new chat in service:', error);
      setChatState(prev => ({ ...prev, initialSystemMessage: null })); // Clear summary even on error
      return null;
    }
  }, [user, messages]); // Keep `messages` dependency for the initial check, though primer effect mostly controls flow

  // Effect to trigger createNewChat when state is primed
  useEffect(() => {
    if (chatState.isLoading && chatState.currentChatId === null) {
      console.log("ChatWindow: Triggering createNewChat. isLoading is true, currentChatId is null. Summary:", chatState.initialSystemMessage);
      createNewChat(chatState.initialSystemMessage || undefined)
        .finally(() => {
          setChatState(prev => ({ ...prev, isLoading: false }));
        });
    }
  }, [chatState.isLoading, chatState.currentChatId, chatState.initialSystemMessage, createNewChat]);

  // Handle sending a message and receiving a response
  const handleSendMessage = useCallback(async () => {
    if (!input.trim() || isProcessing) return;

    const userMessage = { text: input.trim(), sender: 'user' as const };
    let activeChatId = currentChatId;
    let historyForApi: ApiMessage[] = messages.map(msg => ({
      role: msg.sender as 'user' | 'assistant',
      content: msg.text
    }));

    setChatState(prev => ({
      ...prev,
      messages: [...prev.messages, userMessage],
      input: '',
      isTyping: true,
      partialResponse: '',
      inputHeight: 56,
      isProcessing: true,
      initialSystemMessage: null // Clear summary once a message is sent in this flow
    }));
    
    // Check if this is the first message in a new chat session and if there was an initial EHR summary
    // This logic has been mostly moved to createNewChat, triggered by useEffect
    // but we ensure activeChatId is set here if it was just created.

    try {
      if (user) {
        if (!activeChatId) {
          // If a summary was pending, createNewChat would have been called by useEffect
          // If not, create a standard new chat.
          const newId = await createNewChat(chatState.initialSystemMessage || undefined);
          if (newId) activeChatId = newId;
          else {
            // Failed to create new chat, maybe show error and bail
            setChatState(prev => ({ ...prev, isTyping: false, isProcessing: false }));
            return;
          }
        }
        await chatService.addMessageToChat(activeChatId!, userMessage);
        if (typeof window !== 'undefined') window.dispatchEvent(new CustomEvent('refreshChatList'));
      }

      // Prepare history for API, including the system message if it was for this new chat
      if (chatState.initialSystemMessage && messages.length === 0) { // Current `messages` is before adding `userMessage`
         // This implies the chat was just created with the system message implicitly
         // The createNewChat should handle passing this to the chatService if needed
         // For the direct API call here, we might need to prepend it if not already part of `messages`.
         // A better way: ensure `createNewChat` already sets up the context in Firebase if possible,
         // or the API call itself knows how to look for an initial system message based on chat ID state.
         // For now, if initialSystemMessage was set, and we are sending the first user message, prepend it.
         historyForApi.unshift({ role: 'system', content: `EHR Summary for context: ${chatState.initialSystemMessage}` })
      }

      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userMessage.text,
          history: historyForApi // historyForApi now includes the system message if applicable
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
  }, [input, messages, isProcessing, user, currentChatId, initialSystemMessage]);

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

  // Function to handle opening delete confirmation dialog
  const handleOpenDeleteDialog = useCallback(() => {
    setChatState(prev => ({ ...prev, isDeleteDialogOpen: true }));
  }, []);

  // Function to handle closing delete confirmation dialog
  const handleCloseDeleteDialog = useCallback(() => {
    setChatState(prev => ({ ...prev, isDeleteDialogOpen: false }));
  }, []);

  // Function to delete the current chat
  const handleDeleteChat = useCallback(async () => {
    if (!user || !currentChatId || isDeleting) return;
    
    try {
      setChatState(prev => ({ ...prev, isDeleting: true }));
      
      // Call the chatService to delete the chat
      await chatService.deleteChat(currentChatId);
      
      // Create a new chat after deletion
      setChatState(prev => ({
        ...prev,
        messages: [],
        currentChatId: null,
        isDeleteDialogOpen: false,
        isDeleting: false,
        isLoading: true // This will trigger the createNewChat effect
      }));
      
      // Refresh chat list in sidebar
      if (typeof window !== 'undefined') {
        window.dispatchEvent(new CustomEvent('refreshChatList'));
      }
    } catch (error) {
      console.error('Error deleting chat:', error);
      setChatState(prev => ({ 
        ...prev, 
        isDeleteDialogOpen: false, 
        isDeleting: false 
      }));
    }
  }, [user, currentChatId, isDeleting]);

  // Make loadChat and createNewChat available globally
  useEffect(() => {
    if (typeof window !== 'undefined') {
      // @ts-ignore
      window.loadChat = loadChat;
      // @ts-ignore
      window.createNewChat = () => createNewChat(consumeEhrSummary() || undefined);
      // @ts-ignore
      window.deleteCurrentChat = () => {
        if (currentChatId) {
          handleOpenDeleteDialog();
        }
      };
    }
  }, [loadChat, createNewChat, consumeEhrSummary, currentChatId, handleOpenDeleteDialog]);

  // Expose createNewChat globally for the sidebar, potentially passing the summary
  useEffect(() => {
    if (typeof window !== 'undefined') {
      (window as any).createNewChat = () => createNewChat(consumeEhrSummary() || undefined);
    }
    // Cleanup
    return () => {
      if (typeof window !== 'undefined') {
        delete (window as any).createNewChat;
      }
    };
  }, [createNewChat, consumeEhrSummary]); // Add consumeEhrSummary to dependencies

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
        
        {/* Add Delete Chat Button if user is authenticated and there's a current chat */}
        {user && currentChatId && messages.length > 0 && (
          <div className="absolute top-0 right-0 mt-4 mr-4 z-10">
            <button
              onClick={handleOpenDeleteDialog}
              disabled={isDeleting}
              title="Delete this chat"
              className={`p-2 rounded-full text-dukeBlue hover:bg-trueBlue focus:outline-none focus:ring-2 focus:ring-dukeBlue transition-colors ${
                isDeleting ? 'opacity-50 cursor-not-allowed' : ''
              }`}
            >
              <IconTrash className="h-5 w-5" />
            </button>
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

      {/* Delete Confirmation Dialog */}
      {isDeleteDialogOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
          <div className="bg-white rounded-lg p-6 max-w-sm mx-4 shadow-xl">
            <h3 className="text-lg font-medium text-dukeBlue mb-4">Delete Chat</h3>
            <p className="text-sm text-mountbattenPink mb-6">
              Are you sure you want to delete this chat? This action cannot be undone.
            </p>
            <div className="flex justify-end space-x-3">
              <button
                onClick={handleCloseDeleteDialog}
                disabled={isDeleting}
                className="px-4 py-2 text-sm font-medium text-mountbattenPink bg-trueBlue rounded-md hover:bg-opacity-80 focus:outline-none focus:ring-2 focus:ring-dukeBlue"
              >
                Cancel
              </button>
              <button
                onClick={handleDeleteChat}
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
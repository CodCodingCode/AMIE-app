'use client'; // This indicates this is a client-side component in Next.js

import React, { useState, useRef, useEffect, useCallback } from 'react';
// Importing React and necessary hooks:
// - useState: for managing component state
// - useRef: for referencing DOM elements
// - useEffect: for side effects like scrolling
// - useCallback: for optimizing function performance

import { IconRobot, IconSend, IconBrandGoogle } from '@tabler/icons-react'; // Importing a robot icon and other icons
import { ColourfulText } from './colourful';
import TextareaAutosize from 'react-textarea-autosize';
import { motion, AnimatePresence } from 'framer-motion';

// Defining TypeScript types for our messages
type MessageSender = 'user' | 'assistant'; // Message can be from user or assistant
type Message = { text: string; sender: MessageSender }; // A message has text and a sender
// API message format
type ApiMessage = {
  role: 'user' | 'assistant' | 'system';
  content: string;
};

export default function ChatWindow() {
  // State management for our chat application
  // This single state object contains:
  //   - messages: array of chat messages
  //   - input: current text in the input field
  //   - isTyping: whether the assistant appears to be typing
  //   - partialResponse: for storing streaming response text
  //   - inputHeight: for tracking textarea height
  //   - isProcessing: for preventing multiple simultaneous requests
  const [chatState, setChatState] = useState<{
    messages: Message[];
    input: string;
    isTyping: boolean;
    partialResponse: string;
    inputHeight: number;
    isProcessing: boolean;
  }>({ messages: [], input: '', isTyping: false, partialResponse: '', inputHeight: 56, isProcessing: false });
  
  // Creating a reference to the bottom of our messages container
  // This will be used for auto-scrolling
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const chatContainerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  
  // Destructuring our state for easier access
  const { messages, input, isTyping, partialResponse, inputHeight, isProcessing } = chatState;

  // Auto-scroll effect: whenever messages or typing status changes,
  // scroll to the bottom of the chat
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isTyping, partialResponse]); 

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
    if (!input.trim() || isProcessing) return; // Don't send if input is empty or processing

    // Add the user's message to the chat and reset input
    const userMessage = { text: input.trim(), sender: 'user' as const };
    setChatState(prev => ({ 
      ...prev, 
      messages: [...prev.messages, userMessage], // Add user message to chat
      input: '', // Clear input field
      isTyping: true, // Show typing indicator
      partialResponse: '',
      inputHeight: 56, // Reset input height
      isProcessing: true // Set processing flag
    }));

    try {
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

      // Process the stream using the ReadableStream API
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let accumulatedText = '';

      while (true) {
        const { done, value } = await reader.read();
        
        if (done) {
          // Finalize the message when stream is done
          setChatState(prev => ({
            ...prev,
            messages: [...prev.messages, { 
              text: accumulatedText, 
              sender: 'assistant' 
            }],
            isTyping: false,
            partialResponse: '',
            isProcessing: false // Clear processing flag
          }));
          break;
        }
        
        // Decode and append the new chunk
        const chunkText = decoder.decode(value, { stream: true });
        accumulatedText += chunkText;
        
        // Show the partial response in real-time
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
        isProcessing: false // Clear processing flag on error
      }));
    }
  }, [input, messages, isProcessing]); // This function recreates when input or messages change

  // Function to render each message bubble
  const renderMessage = useCallback((message: Message, index: number) => (
    <div
      key={index}
      className={`message mb-6 animate-fadeIn ${
        message.sender === 'user' ? 'flex justify-end' : ''
      }`}
    >
      {message.sender === 'user' ? (
        // User message - displayed in dark bubble at top right
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
        <div className="flex-1 overflow-y-auto pb-32 scrollbar-hide">
          {/* Display all messages */}
          {messages.map(renderMessage)}

          {/* Welcome message - shown only when there are no messages */}
          {messages.length === 0 && (
            <div className="text-center fixed top-1/3 left-0 right-0 z-0 pointer-events-none">
                <h1 className="font-bold" style={{ fontSize: '5em' }}> Welcome to the </h1>
                <ColourfulText text="Bluebox" />
            </div>
          )}

          {/* Streaming response - shown while receiving chunks */}
          {partialResponse && (
            <div className="message mb-6 animate-fadeIn">
              <div className="max-w-full text-gray-800 dark:text-gray-200 py-2 text-lg leading-relaxed">
                <p className="whitespace-pre-wrap">{partialResponse}</p>
              </div>
            </div>
          )}

          {/* Typing indicator - animated dots shown when assistant is "typing" but no text yet */}
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
          {/* This empty div is used as a reference point for auto-scrolling */}
          <div ref={messagesEndRef} />
        </div>

        {/* Message input area - fixed at bottom of screen */}
        <div className="fixed bottom-0 left-0 right-0 z-10">
            <div className="max-w-5xl mx-auto px-4">
                <motion.div
                className="mb-6 bg-gray-100 dark:bg-neutral-900 w-full rounded-t-xl pt-6"
                style={{ 
                    transformOrigin: "bottom",
                    position: "relative" 
                }}
                >
                <div className="flex bg-white dark:bg-neutral-800 border border-black dark:border-neutral-600 rounded-3xl shadow-sm focus-within:shadow-md transition-shadow duration-300 px-4">
                    <div className="flex-1 flex flex-col justify-end">
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
                        placeholder="Ask your health question..."
                        className="py-4 px-2 bg-transparent focus:outline-none resize-none text-black dark:text-white min-h-[144px] max-h-[200px] overflow-auto"
                        minRows={1}
                        maxRows={8}
                        disabled={isProcessing}
                    />
                    </div>

                    {/* Send button pinned to bottom */}
                    <div className="flex items-end pb-4 pl-2">
                    <button
                        onClick={handleSendMessage}
                        disabled={!input.trim() || isProcessing}
                        className={`p-2 rounded-full ${
                        !input.trim() || isProcessing
                            ? 'text-gray-400'
                            : 'text-blue-500 hover:bg-blue-50 dark:hover:bg-neutral-700'
                        } transition-colors`}
                    >
                        {isProcessing ? (
                        <div className="h-6 w-6 relative">
                            <IconBrandGoogle className="h-6 w-6 absolute" />
                            <div className="h-6 w-6 absolute rounded-full border-2 border-t-blue-500 border-r-transparent border-b-transparent border-l-transparent animate-spin" />
                        </div>
                        ) : (
                        <IconSend className="h-6 w-6" />
                        )}
                    </button>
                    </div>
                </div>
                </motion.div>
            </div>
        </div>
      </div>
    </div>
  );
}
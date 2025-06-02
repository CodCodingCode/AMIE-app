'use client';

import React, { useState, useRef, useEffect, useCallback, useMemo } from 'react';
import { useSearchParams } from 'next/navigation';
import { IconSend, IconUser, IconSparkles } from '@tabler/icons-react';
import { ColourfulText } from './colourful';
import TextareaAutosize from 'react-textarea-autosize';
import { useAuth, AuthButton } from './Auth';
import { chatService, ChatMessage as ServiceChatMessage, Chat } from './chatService';
import { dispatchCustomEvent, formatDate } from '@/app/lib/utils';
import { useGlobalFunctions } from '@/app/lib/hooks';
import { motion, AnimatePresence } from 'framer-motion';

type MessageSender = 'user' | 'assistant';
type Message = { text: string; sender: MessageSender; timestamp?: Date };
type ApiMessage = { role: 'user' | 'assistant' | 'system'; content: string };

const TypingIndicator = () => (
  <div className="flex items-center space-x-2 mb-6">
    <IconSparkles className="w-5 h-5 text-blue-500 animate-pulse" />
    <p className="text-sm text-gray-500 dark:text-gray-400">Assistant is typing...</p>
  </div>
);

const WelcomeMessage = () => (
  <motion.div 
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    className="text-center py-12"
  >
    <h1 className="text-3xl font-bold text-gray-800 dark:text-white mb-2">
      Welcome to <span className="text-blue-600 dark:text-blue-400">Bluebox</span>
    </h1>
    <p className="text-lg text-gray-600 dark:text-gray-400 mb-8">
      How can I help you today?
    </p>
    <ColourfulText text="Bluebox AI" size="large" />
  </motion.div>
);

const MessageBubble: React.FC<{ message: Message, index: number }> = ({ message, index }) => {
  const isUser = message.sender === 'user';
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: index * 0.05 }}
      className={`flex mb-4 ${isUser ? 'justify-end' : 'justify-start'}`}
    >
      <div className={`p-3 rounded-lg max-w-lg lg:max-w-xl xl:max-w-2xl shadow-md ${isUser 
        ? 'bg-blue-600 text-white rounded-br-none' 
        : 'bg-neutral-700 text-gray-200 rounded-bl-none'
      }`}>
        <p className="text-sm whitespace-pre-wrap">{message.text}</p>
        {message.timestamp && (
          <p className={`text-xs mt-1 ${isUser ? 'text-blue-200' : 'text-gray-400'} text-right`}>
            {formatDate(message.timestamp)}
          </p>
        )}
      </div>
    </motion.div>
  );
};

export default function ChatWindow() {
  const { user, loading: authLoading } = useAuth();
  const searchParams = useSearchParams();
  const urlChatId = searchParams.get('id');
  
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [currentChatId, setCurrentChatId] = useState<string | null>(urlChatId);
  const [isLoading, setIsLoading] = useState(!!urlChatId);
  const [error, setError] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const handleApiStream = async (reader: ReadableStreamDefaultReader<Uint8Array>, chatIdToUpdate: string) => {
    const decoder = new TextDecoder();
    let accumulatedText = '';
    setMessages(prev => [...prev, { text: '', sender: 'assistant' }]); // Add empty assistant message for streaming

    while (true) {
      const { done, value } = await reader.read();
      if (done) {
        setIsTyping(false);
        if (user) {
          await chatService.addMessageToChat(chatIdToUpdate, { text: accumulatedText, sender: 'assistant' });
          dispatchCustomEvent('refreshChatList');
        }
        break;
      }
      accumulatedText += decoder.decode(value, { stream: true });
      setMessages(prev => 
        prev.map((msg, i) => i === prev.length -1 ? { ...msg, text: accumulatedText, timestamp: new Date() } : msg)
      );
    }
  };

  const processSendMessage = async (text: string, currentChatIdToUse: string | null) => {
    setIsTyping(true);
    setError(null);
    let activeChatId = currentChatIdToUse;

    try {
      if (user) {
        if (!activeChatId) {
          const newId = await chatService.createNewChat(user);
          if (!newId) throw new Error('Failed to create new chat.');
          activeChatId = newId;
          setCurrentChatId(newId);
          dispatchCustomEvent('refreshChatList');
          dispatchCustomEvent('currentChatUpdate', { detail: { chatId: newId } });
        }
        await chatService.addMessageToChat(activeChatId, { text, sender: 'user' });
      }

      const historyForApi: ApiMessage[] = messages.map(msg => ({ role: msg.sender, content: msg.text }));
      historyForApi.push({role: 'user', content: text}); // Add current user message to history for API call

      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, history: historyForApi }),
      });

      if (!response.ok || !response.body) throw new Error(`Server error: ${response.status}`);
      if (!activeChatId) throw new Error('Chat ID became null during processing');

      await handleApiStream(response.body.getReader(), activeChatId);

    } catch (err: any) {
      console.error('Error sending message:', err);
      setError(err.message || 'Failed to send message');
      setIsTyping(false);
    }
  };

  const handleSendMessage = () => {
    const trimmedInput = input.trim();
    if (!trimmedInput || isTyping) return;
    
    const userMessage: Message = { text: trimmedInput, sender: 'user', timestamp: new Date() };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    processSendMessage(trimmedInput, currentChatId);
  };

  const loadChat = useCallback(async (chatId: string) => {
    if (!user) {
      setIsLoading(false);
      return;
    }
    setIsLoading(true);
    setError(null);
    try {
      const chat = await chatService.getChat(chatId);
      if (chat) {
        setMessages(chat.messages.map(msg => ({ text: msg.text, sender: msg.sender as MessageSender, timestamp: msg.timestamp })));
        setCurrentChatId(chat.id);
        dispatchCustomEvent('currentChatUpdate', { detail: { chatId: chat.id } });
      } else {
        setError('Chat not found.');
        setMessages([]);
        setCurrentChatId(null);
        // Optionally, redirect or show a clear "chat not found" message
        // router.replace('/chat'); // If using next/router
      }
    } catch (err: any) {
      console.error('Error loading chat:', err);
      setError(err.message || 'Failed to load chat');
    } finally {
      setIsLoading(false);
    }
  }, [user]);

  const createNewChat = useCallback(async () => {
    if (!user) {
      setMessages([]);
      setCurrentChatId(null);
      dispatchCustomEvent('refreshChatList');
      dispatchCustomEvent('currentChatUpdate', { detail: { chatId: null }});
      // Consider prompting for sign-in
      return;
    }
    setIsLoading(true);
    setError(null);
    try {
      const newChatId = await chatService.createNewChat(user);
      setMessages([]);
      setCurrentChatId(newChatId);
      dispatchCustomEvent('refreshChatList');
      dispatchCustomEvent('currentChatUpdate', { detail: { chatId: newChatId } });
      if (typeof window !== 'undefined') {
        // Update URL without full page reload for better UX
        history.pushState({}, '', `/chat?id=${newChatId}`);
      }
    } catch (err: any) {
      console.error('Error creating new chat:', err);
      setError(err.message || 'Failed to create chat');
    } finally {
      setIsLoading(false);
    }
  }, [user]);

  // Effect for URL changes
  useEffect(() => {
    if (urlChatId && urlChatId !== currentChatId) {
      loadChat(urlChatId);
    } else if (!urlChatId && currentChatId) {
      // Navigated away from a specific chat to /chat (new chat implicitly)
      setMessages([]);
      setCurrentChatId(null);
      setError(null);
      setIsLoading(false); 
    } else if (!urlChatId && !currentChatId && !isLoading && user) {
      // If at /chat, no current chat ID, not loading, and user is logged in, create one automatically
      // This might be too aggressive, consider a button or a more explicit action
      // createNewChat(); 
    } else if (!user && !authLoading) {
      // User signed out or not logged in, clear chat state
      setMessages([]);
      setCurrentChatId(null);
      setIsLoading(false);
    }
  }, [urlChatId, user, authLoading, currentChatId, loadChat, isLoading]);
 
  // Expose loadChat and createNewChat globally (used by sidebar)
  useGlobalFunctions(useMemo(() => ({ loadChat, createNewChat }), [loadChat, createNewChat]));

  useEffect(scrollToBottom, [messages, isTyping]);

  // Focus input on initial load or when chat ID changes
  useEffect(() => {
    if (inputRef.current && (!isLoading || currentChatId)) {
      inputRef.current.focus();
    }
  }, [isLoading, currentChatId]);

  const showWelcomeMessage = !isLoading && messages.length === 0 && !isTyping && !error;

  return (
    <div className="flex flex-col h-screen bg-neutral-900 text-white">
      <div className="flex-1 flex flex-col max-w-3xl mx-auto w-full px-4 pt-6 pb-20 relative overflow-hidden">
        {!user && !authLoading && (
          <motion.div initial={{opacity:0, y: -10}} animate={{opacity:1, y:0}} className="bg-blue-900/30 border border-blue-700/50 rounded-lg p-3 mb-4 flex items-center justify-between text-sm">
            <p className="text-blue-200">
              Sign in to save your chat history and access more features.
            </p>
            <AuthButton />
          </motion.div>
        )}

        <AnimatePresence mode="wait">
          {isLoading && (
            <motion.div key="loader" initial={{opacity:0}} animate={{opacity:1}} exit={{opacity:0}} className="flex flex-col items-center justify-center h-full">
              <div className="flex items-center space-x-2 text-gray-400">
                <div className="w-2 h-2 bg-current rounded-full animate-bounce [animation-delay:-0.3s]"></div>
                <div className="w-2 h-2 bg-current rounded-full animate-bounce [animation-delay:-0.15s]"></div>
                <div className="w-2 h-2 bg-current rounded-full animate-bounce"></div>
              </div>
              <p className="mt-2 text-sm">
                {currentChatId ? "Loading chat..." : "Initializing chat..."}
              </p>
            </motion.div>
          )}
        </AnimatePresence>

        {!isLoading && error && (
          <motion.div initial={{opacity:0}} animate={{opacity:1}} className="text-center py-10 text-red-400 bg-red-900/30 p-4 rounded-md">
            <p>Error: {error}</p>
            <button onClick={() => urlChatId ? loadChat(urlChatId) : createNewChat()} className="mt-2 px-4 py-2 bg-red-600 hover:bg-red-700 rounded text-white">
              Retry
            </button>
          </motion.div>
        )}
        
        {!isLoading && !error && (
          <div className="flex-1 overflow-y-auto no-scrollbar space-y-4 pr-2 -mr-2">
            {showWelcomeMessage ? <WelcomeMessage /> : messages.map((msg, index) => (
              <MessageBubble key={`${currentChatId || 'new'}-${index}`} message={msg} index={index} />
            ))}
            {isTyping && <TypingIndicator />}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {!isLoading && !error && (
        <div className="fixed bottom-0 left-0 right-0 bg-neutral-900/80 backdrop-blur-md">
          <div className="max-w-3xl mx-auto px-4 py-3 sm:py-4">
            <div className="flex items-center bg-neutral-800 border border-neutral-700 rounded-xl shadow-lg p-1">
              <TextareaAutosize
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSendMessage();
                  }
                }}
                placeholder={user ? "Ask Bluebox anything..." : "Sign in to start chatting..."}
                className="flex-1 p-3 bg-transparent text-white placeholder-gray-500 focus:outline-none resize-none no-scrollbar"
                minRows={1}
                maxRows={5}
                disabled={isTyping || !user && !authLoading}
              />
              <button
                onClick={handleSendMessage}
                disabled={isTyping || !input.trim() || (!user && !authLoading)}
                className="p-3 rounded-lg text-white bg-blue-600 hover:bg-blue-700 disabled:bg-neutral-600 disabled:text-gray-400 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:cursor-not-allowed ml-2"
                aria-label="Send message"
              >
                <IconSend size={20} />
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
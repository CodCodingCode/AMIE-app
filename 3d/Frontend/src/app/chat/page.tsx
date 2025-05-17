'use client';

import React, { useState, useRef, useEffect } from 'react';
import { IconRobot, IconBrandTabler, IconUserBolt, IconSettings, IconArrowLeft } from '@tabler/icons-react';
import { Sidebar, SidebarBody, SidebarLink } from './sidebar';
import { motion } from 'motion/react';

interface Message {
  text: string;
  sender: 'user' | 'assistant';
}

// Logo components from SidebarDemo
const Logo = () => {
  return (
    <a
      href="#"
      className="relative z-20 flex items-center space-x-2 py-1 text-sm font-normal text-black"
    >
      <div className="h-5 w-6 shrink-0 rounded-tl-lg rounded-tr-sm rounded-br-lg rounded-bl-sm bg-black dark:bg-white" />
      <motion.span
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="font-medium whitespace-pre text-black dark:text-white"
      >
        AMIE Health
      </motion.span>
    </a>
  );
};

const LogoIcon = () => {
  return (
    <a
      href="#"
      className="relative z-20 flex items-center space-x-2 py-1 text-sm font-normal text-black"
    >
      <div className="h-5 w-6 shrink-0 rounded-tl-lg rounded-tr-sm rounded-br-lg rounded-bl-sm bg-black dark:bg-white" />
    </a>
  );
};

export default function Chat() {
  // State to store chat messages
  const [messages, setMessages] = useState<Message[]>([]);
  // State to store the current input text
  const [input, setInput] = useState('');
  // State to track when the assistant is typing
  const [isTyping, setIsTyping] = useState(false);
  // Reference to automatically scroll to the latest message
  const messagesEndRef = useRef<HTMLDivElement>(null);
  // State for sidebar visibility
  const [sidebarOpen, setSidebarOpen] = useState(false);

  // Define sidebar links
  const links = [
    {
      label: "Dashboard",
      href: "#",
      icon: (
        <IconBrandTabler className="h-5 w-5 shrink-0 text-neutral-700 dark:text-neutral-200" />
      ),
    },
    {
      label: "Profile",
      href: "#",
      icon: (
        <IconUserBolt className="h-5 w-5 shrink-0 text-neutral-700 dark:text-neutral-200" />
      ),
    },
    {
      label: "Settings",
      href: "#",
      icon: (
        <IconSettings className="h-5 w-5 shrink-0 text-neutral-700 dark:text-neutral-200" />
      ),
    },
    {
      label: "Logout",
      href: "#",
      icon: (
        <IconArrowLeft className="h-5 w-5 shrink-0 text-neutral-700 dark:text-neutral-200" />
      ),
    },
  ];

  // Auto-scroll to the bottom whenever messages change or typing status changes
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    e.target.style.height = 'auto';
    e.target.style.height = `${e.target.scrollHeight}px`;
  };  

  // Send message to the backend API and handle the response
  const handleSendMessage = async () => {
    if (input.trim() === '') return;

    // Add user message to the chat
    const userMessage: Message = { text: input.trim(), sender: 'user' };
    setMessages(prev => [...prev, userMessage]);
    setInput('');

    // Show typing indicator while waiting for response
    setIsTyping(true);

    // Send request to the backend
    const response = await fetch('http://localhost:5001/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: userMessage.text,
      }),
    });

    setIsTyping(false);

    // Add assistant's response to the chat
    const data = await response.json();
    const assistantMessage: Message = {
      text: data.response,
      sender: 'assistant',
    };

    setMessages(prev => [...prev, assistantMessage]);
  };

  return (
    <div className="flex h-screen bg-gray-100 dark:bg-neutral-900">
      {/* Sidebar */}
      <Sidebar open={sidebarOpen} setOpen={setSidebarOpen}>
        <SidebarBody className="justify-between gap-10">
          <div className="flex flex-1 flex-col overflow-x-hidden overflow-y-auto">
            {sidebarOpen ? <Logo /> : <LogoIcon />}
            <div className="mt-8 flex flex-col gap-2">
              {links.map((link, idx) => (
                <SidebarLink key={idx} link={link} />
              ))}
            </div>
          </div>
          <div>
            <SidebarLink
              link={{
                label: "Your Profile",
                href: "#",
                icon: (
                  <div className="h-7 w-7 shrink-0 rounded-full bg-neutral-300 dark:bg-neutral-600 grid place-items-center">
                    <span className="text-xs text-neutral-700 dark:text-neutral-200">U</span>
                  </div>
                ),
              }}
            />
          </div>
        </SidebarBody>
      </Sidebar>
      
      {/* Main Chat Content */}
      <div className="flex-1 flex flex-col">
        <div
          className={`flex-1 flex ${
            messages.length === 0 ? 'items-center justify-center' : 'flex-col'
          } max-w-4xl mx-auto w-full px-4 relative`}
        >
          {/* Messages container with scroll */}
          <div className="flex-1 overflow-y-auto py-4">
            {/* Map through and display all messages */}
            {messages.map((message, i) => (
              <div
                key={i}
                className={`message mb-6 animate-fadeIn ${
                  message.sender === 'user' ? 'flex justify-start' : ''
                }`}
              >
                {message.sender === 'user' ? (
                  <div className="max-w-xs bg-gray-800 text-white p-4 rounded-2xl rounded-tl-sm shadow-sm">
                    <p className="text-sm whitespace-pre-wrap">{message.text}</p>
                  </div>
                ) : (
                  <div className="max-w-full text-gray-800 dark:text-gray-200 py-2 text-lg leading-relaxed">
                    <p className="whitespace-pre-wrap">{message.text}</p>
                  </div>
                )}
              </div>
            ))}

            {/* Empty state when no messages */}
            {messages.length === 0 && (
              <div className="text-center">
                <div className="flex justify-center mb-4">
                  <IconRobot className="w-16 h-16 text-neutral-400" />
                </div>
                <h2 className="text-xl font-semibold text-neutral-700 dark:text-neutral-300 mb-2">
                  Welcome to AMIE Assistant
                </h2>
                <p className="text-neutral-500 dark:text-neutral-400 max-w-md mx-auto">
                  Ask me any health-related questions and I'll do my best to help you.
                </p>
              </div>
            )}

            {/* Typing indicator animation */}
            {isTyping && (
              <div className="mb-6">
                <div className="flex space-x-2 py-2">
                  <div className="w-2 h-2 rounded-full bg-gray-400 animate-bounce"></div>
                  <div
                    className="w-2 h-2 rounded-full bg-gray-400 animate-bounce"
                    style={{ animationDelay: '0.2s' }}
                  ></div>
                  <div
                    className="w-2 h-2 rounded-full bg-gray-400 animate-bounce"
                    style={{ animationDelay: '0.4s' }}
                  ></div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Message input area */}
          <div className="py-6 sticky bottom-0 bg-gray-100 dark:bg-neutral-900 w-full">
            <div className="flex items-center bg-white dark:bg-neutral-800 border border-black dark:border-neutral-600 rounded-2xl shadow-sm focus-within:shadow-md transition-shadow duration-300 px-4">
              <textarea
                value={input}
                onChange={handleInputChange}
                onKeyDown={e => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSendMessage();
                  }
                }}
                placeholder="Ask your health question..."
                className="flex-1 py-4 px-2 bg-transparent focus:outline-none resize-none text-black dark:text-white min-h-[144px] max-h-[200px] overflow-auto"
                rows={1}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
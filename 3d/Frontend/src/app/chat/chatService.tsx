'use client';

import { db } from '@/app/firebase';
import { collection, addDoc, getDocs, query, where, orderBy, doc, updateDoc, arrayUnion, getDoc, Timestamp } from 'firebase/firestore';
import { User } from 'firebase/auth';

export type ChatMessage = {
  text: string;
  sender: 'user' | 'assistant';
  timestamp: Date;
};

export type Chat = {
  id: string;
  title: string;
  userId: string;
  createdAt: Date;
  updatedAt: Date;
  messages: ChatMessage[];
};

export const chatService = {
  async createNewChat(user: User): Promise<string> {
    try {
      const chatRef = await addDoc(collection(db, 'chats'), {
        userId: user.uid,
        title: 'New Chat',
        createdAt: Timestamp.now(),
        updatedAt: Timestamp.now(),
        messages: []
      });
      return chatRef.id;
    } catch (error) {
      console.error('Error creating new chat:', error);
      throw error;
    }
  },

  async getUserChats(user: User): Promise<Chat[]> {
    try {
      const q = query(
        collection(db, 'chats'),
        where('userId', '==', user.uid),
        orderBy('updatedAt', 'desc')
      );
      
      const querySnapshot = await getDocs(q);
      
      return querySnapshot.docs.map(doc => {
        const data = doc.data();
        return {
          id: doc.id,
          title: data.title,
          userId: data.userId,
          createdAt: data.createdAt.toDate(),
          updatedAt: data.updatedAt.toDate(),
          messages: (data.messages || []).map((msg: any) => ({
            ...msg,
            timestamp: msg.timestamp?.toDate() || new Date()
          }))
        };
      });
    } catch (error) {
      console.error('Error getting user chats:', error);
      return [];
    }
  },

  async getChat(chatId: string): Promise<Chat | null> {
    try {
      const chatDoc = await getDoc(doc(db, 'chats', chatId));
      if (!chatDoc.exists()) return null;
      
      const data = chatDoc.data();
      return {
        id: chatDoc.id,
        title: data.title,
        userId: data.userId,
        createdAt: data.createdAt.toDate(),
        updatedAt: data.updatedAt.toDate(),
        messages: (data.messages || []).map((msg: any) => ({
          ...msg,
          timestamp: msg.timestamp?.toDate() || new Date()
        }))
      };
    } catch (error) {
      console.error('Error getting chat:', error);
      return null;
    }
  },

  async addMessageToChat(chatId: string, message: Omit<ChatMessage, 'timestamp'>): Promise<void> {
    try {
      const chatRef = doc(db, 'chats', chatId);
      
      // Create message with timestamp
      const messageWithTimestamp = {
        ...message,
        timestamp: Timestamp.now()
      };
      
      // Update the chat document
      await updateDoc(chatRef, {
        messages: arrayUnion(messageWithTimestamp),
        updatedAt: Timestamp.now(),
        // Always update title with user messages for better identification in sidebar
        ...(message.sender === 'user' && messageWithTimestamp.text.length > 0 
          ? { title: messageWithTimestamp.text.slice(0, 30) + (messageWithTimestamp.text.length > 30 ? '...' : '') } 
          : {})
      });
    } catch (error) {
      console.error('Error adding message to chat:', error);
      throw error;
    }
  }
};
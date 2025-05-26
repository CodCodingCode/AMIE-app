'use client';

import { db } from '@/app/firebase';
import { collection, addDoc, getDocs, query, where, orderBy, doc, updateDoc, arrayUnion, getDoc, deleteDoc, Timestamp } from 'firebase/firestore';
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
      
      const messageWithTimestamp = {
        ...message,
        timestamp: Timestamp.now()
      };
      
      await updateDoc(chatRef, {
        messages: arrayUnion(messageWithTimestamp),
        updatedAt: Timestamp.now(),
        ...(message.sender === 'user' && messageWithTimestamp.text.length > 0 
          ? { title: messageWithTimestamp.text.slice(0, 30) + (messageWithTimestamp.text.length > 30 ? '...' : '') } 
          : {})
      });
    } catch (error) {
      console.error('Error adding message to chat:', error);
      throw error;
    }
  },

  async deleteChat(chatId: string): Promise<void> {
    try {
      await deleteDoc(doc(db, 'chats', chatId));
    } catch (error) {
      console.error('Error deleting chat:', error);
      throw error;
    }
  },

  async cleanupEmptyChats(user: User): Promise<void> {
    try {
      const chats = await this.getUserChats(user);
      const emptyChats = chats.filter(chat => chat.messages.length === 0);
      
      // Delete all empty chats
      const deletePromises = emptyChats.map(chat => this.deleteChat(chat.id));
      await Promise.all(deletePromises);
      
      console.log(`Cleaned up ${emptyChats.length} empty chats`);
    } catch (error) {
      console.error('Error cleaning up empty chats:', error);
      throw error;
    }
  }
};
'use client';

import { db } from '@/app/firebase';
import {
  collection, addDoc, getDocs, query, where, orderBy, doc, updateDoc, arrayUnion, getDoc, deleteDoc, Timestamp, runTransaction, writeBatch, DocumentData, QueryDocumentSnapshot
} from 'firebase/firestore';
import { User } from 'firebase/auth';
import { truncateText } from '@/app/lib/utils';

export type ChatMessage = {
  text: string;
  sender: 'user' | 'assistant';
  timestamp: Date;
};

export type ConsultationStatus = 'new' | 'in-progress' | 'completed' | 'archived';
export type ConsultationPriority = 'low' | 'medium' | 'high' | 'urgent';

export interface ConsultationMetadata {
  status: ConsultationStatus;
  priority: ConsultationPriority;
  category: string;
  tags: string[];
  soapGenerated: boolean;
  lastActionDate: Date;
  referrals?: string[];
  followUps?: string[];
}

export type Chat = {
  id: string;
  title: string;
  userId: string;
  createdAt: Date;
  updatedAt: Date;
  messages: ChatMessage[];
  metadata?: ConsultationMetadata;
};

export interface SOAPNote {
  id: string;
  chatId: string;
  subjective: string;
  objective: string;
  assessment: string;
  plan: string[];
  generatedAt: Date;
  generatedBy: string;
}

export interface Referral {
  id: string;
  chatId: string;
  patientId: string;
  referralTo: string;
  urgency: 'routine' | 'urgent';
  reason: string;
  symptoms: string[];
  clinicalSummary: string;
  status: 'pending' | 'sent' | 'completed';
  createdAt: Date;
}

export interface FollowUp {
  id: string;
  chatId: string;
  patientId: string;
  scheduledDate: Date;
  type: 'follow-up' | 'lab-results' | 'medication-check' | 'specialist-consultation';
  reason: string;
  status: 'scheduled' | 'completed' | 'cancelled';
  notes?: string;
  createdAt: Date;
}

const chatsCollection = collection(db, 'chats');
const soapNotesCollection = collection(db, 'soapNotes');
const referralsCollection = collection(db, 'referrals');
const followUpsCollection = collection(db, 'followUps');

async function handleFirestoreOperation<T>(operation: () => Promise<T>, errorMessage: string): Promise<T> {
  try {
    return await operation();
  } catch (error) {
    console.error(errorMessage, error);
    throw error;
  }
}

function docToChat(docSnap: QueryDocumentSnapshot<DocumentData>): Chat {
  const data = docSnap.data();
  return {
    id: docSnap.id,
    title: data.title,
    userId: data.userId,
    createdAt: (data.createdAt as Timestamp)?.toDate() || new Date(),
    updatedAt: (data.updatedAt as Timestamp)?.toDate() || new Date(),
    messages: (data.messages || []).map((msg: any) => ({
      ...msg,
      timestamp: (msg.timestamp as Timestamp)?.toDate() || new Date(),
    })),
    metadata: data.metadata ? {
      ...data.metadata,
      lastActionDate: (data.metadata.lastActionDate as Timestamp)?.toDate() || new Date(),
    } : undefined,
  };
}

export const chatService = {
  async createNewChat(user: User): Promise<string> {
    return handleFirestoreOperation(async () => {
      const chatRef = await addDoc(chatsCollection, {
        userId: user.uid,
        title: 'New Chat',
        createdAt: Timestamp.now(),
        updatedAt: Timestamp.now(),
        messages: [],
        metadata: {
          status: 'new',
          priority: 'medium',
          category: 'General',
          tags: [],
          soapGenerated: false,
          lastActionDate: Timestamp.now(),
          referrals: [],
          followUps: [],
        },
      });
      return chatRef.id;
    }, 'Error creating new chat');
  },

  async getUserChats(user: User): Promise<Chat[]> {
    return handleFirestoreOperation(async () => {
      const q = query(chatsCollection, where('userId', '==', user.uid), orderBy('updatedAt', 'desc'));
      const querySnapshot = await getDocs(q);
      return querySnapshot.docs.map(docToChat);
    }, 'Error getting user chats');
  },

  async getChat(chatId: string): Promise<Chat | null> {
    return handleFirestoreOperation(async () => {
      const chatDoc = await getDoc(doc(chatsCollection, chatId));
      return chatDoc.exists() ? docToChat(chatDoc as QueryDocumentSnapshot<DocumentData>) : null;
    }, 'Error getting chat');
  },

  async addMessageToChat(chatId: string, message: Omit<ChatMessage, 'timestamp'>): Promise<void> {
    return handleFirestoreOperation(async () => {
      const chatRef = doc(chatsCollection, chatId);
      const messageWithTimestamp = { ...message, timestamp: Timestamp.now() };
      
      const updateData: any = {
        messages: arrayUnion(messageWithTimestamp),
        updatedAt: Timestamp.now(),
        'metadata.lastActionDate': Timestamp.now(),
      };

      if (message.sender === 'user' && message.text.length > 0) {
        updateData.title = truncateText(message.text, 30);
      }

      await updateDoc(chatRef, updateData);
    }, 'Error adding message to chat');
  },

  async deleteChat(chatId: string): Promise<void> {
    return handleFirestoreOperation(async () => {
      await deleteDoc(doc(chatsCollection, chatId));
      // Consider deleting associated SOAP notes, referrals, follow-ups in a transaction or batch
    }, 'Error deleting chat');
  },

  async cleanupEmptyChats(user: User): Promise<void> {
    return handleFirestoreOperation(async () => {
      const chats = await this.getUserChats(user);
      const emptyChats = chats.filter(chat => chat.messages.length === 0);
      
      if (emptyChats.length === 0) {
        console.log('No empty chats to clean up.');
        return;
      }

      const batch = writeBatch(db);
      emptyChats.forEach(chat => batch.delete(doc(chatsCollection, chat.id)));
      await batch.commit();
      console.log(`Cleaned up ${emptyChats.length} empty chats`);
    }, 'Error cleaning up empty chats');
  },

  async updateConsultationMetadata(chatId: string, metadata: Partial<ConsultationMetadata>): Promise<void> {
    return handleFirestoreOperation(async () => {
      const chatRef = doc(chatsCollection, chatId);
      const updateData: any = {
        updatedAt: Timestamp.now(),
        'metadata.lastActionDate': Timestamp.now(),
      };
      for (const [key, value] of Object.entries(metadata)) {
        updateData[`metadata.${key}`] = (key === 'lastActionDate' && value instanceof Date) ? Timestamp.fromDate(value) : value;
      }
      await updateDoc(chatRef, updateData);
    }, 'Error updating consultation metadata');
  },

  async saveSOAPNote(soapNote: Omit<SOAPNote, 'id' | 'generatedAt'>): Promise<string> {
    return handleFirestoreOperation(async () => {
      const soapRef = await addDoc(soapNotesCollection, { ...soapNote, generatedAt: Timestamp.now() });
      await this.updateConsultationMetadata(soapNote.chatId, { soapGenerated: true });
      return soapRef.id;
    }, 'Error saving SOAP note');
  },

  async getSOAPNote(chatId: string): Promise<SOAPNote | null> {
    return handleFirestoreOperation(async () => {
      const q = query(soapNotesCollection, where('chatId', '==', chatId), orderBy('generatedAt', 'desc'));
      const querySnapshot = await getDocs(q);
      if (querySnapshot.empty) return null;
      const docSnap = querySnapshot.docs[0];
      const data = docSnap.data();
      return {
        id: docSnap.id,
        ...data,
        generatedAt: (data.generatedAt as Timestamp).toDate(),
      } as SOAPNote;
    }, 'Error getting SOAP note');
  },

  async createReferral(referral: Omit<Referral, 'id' | 'createdAt'>): Promise<string> {
    return handleFirestoreOperation(async () => {
      const referralRef = await addDoc(referralsCollection, { ...referral, createdAt: Timestamp.now() });
      // Optionally, update chat metadata with referral ID
      await this.updateConsultationMetadata(referral.chatId, {
        referrals: arrayUnion(referralRef.id) as any, // Type assertion needed for arrayUnion
      });
      return referralRef.id;
    }, 'Error creating referral');
  },

  async getReferrals(chatId: string): Promise<Referral[]> {
    return handleFirestoreOperation(async () => {
      const q = query(referralsCollection, where('chatId', '==', chatId), orderBy('createdAt', 'desc'));
      const querySnapshot = await getDocs(q);
      return querySnapshot.docs.map(docSnap => {
        const data = docSnap.data();
        return {
          id: docSnap.id,
          ...data,
          createdAt: (data.createdAt as Timestamp).toDate(),
        } as Referral;
      });
    }, 'Error getting referrals');
  },

  async createFollowUp(followUp: Omit<FollowUp, 'id' | 'createdAt'>): Promise<string> {
    return handleFirestoreOperation(async () => {
      const followUpRef = await addDoc(followUpsCollection, { ...followUp, createdAt: Timestamp.now() });
      // Optionally, update chat metadata with follow-up ID
       await this.updateConsultationMetadata(followUp.chatId, {
        followUps: arrayUnion(followUpRef.id) as any, // Type assertion needed for arrayUnion
      });
      return followUpRef.id;
    }, 'Error creating follow-up');
  },

  async getFollowUps(chatId: string): Promise<FollowUp[]> {
    return handleFirestoreOperation(async () => {
      const q = query(followUpsCollection, where('chatId', '==', chatId), orderBy('createdAt', 'desc'));
      const querySnapshot = await getDocs(q);
      return querySnapshot.docs.map(docSnap => {
        const data = docSnap.data();
        return {
          id: docSnap.id,
          ...data,
          createdAt: (data.createdAt as Timestamp).toDate(),
          scheduledDate: (data.scheduledDate as Timestamp).toDate(),
        } as FollowUp;
      });
    }, 'Error getting follow-ups');
  },

  async getConsultationAnalytics(userId: string): Promise<any> { // Simplified return type for brevity
    return handleFirestoreOperation(async () => {
      const userChats = await this.getUserChats({ uid: userId } as User); // Basic user object
      const now = new Date();
      const oneWeekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);

      const analytics = {
        totalConsultations: userChats.length,
        thisWeek: userChats.filter(c => c.createdAt >= oneWeekAgo).length,
        soapNotesGenerated: userChats.filter(c => c.metadata?.soapGenerated).length,
        referralsMade: userChats.reduce((acc, c) => acc + (c.metadata?.referrals?.length || 0), 0),
        followUpsScheduled: userChats.reduce((acc, c) => acc + (c.metadata?.followUps?.length || 0), 0),
        statusBreakdown: {} as Record<ConsultationStatus, number>,
        categoryBreakdown: {} as Record<string, number>,
        priorityBreakdown: {} as Record<ConsultationPriority, number>,
      };

      userChats.forEach(chat => {
        if (chat.metadata) {
          analytics.statusBreakdown[chat.metadata.status] = (analytics.statusBreakdown[chat.metadata.status] || 0) + 1;
          analytics.categoryBreakdown[chat.metadata.category] = (analytics.categoryBreakdown[chat.metadata.category] || 0) + 1;
          analytics.priorityBreakdown[chat.metadata.priority] = (analytics.priorityBreakdown[chat.metadata.priority] || 0) + 1;
        }
      });
      return analytics;
    }, 'Error getting consultation analytics');
  },

  async bulkUpdateConsultations(
    chatIds: string[], 
    operation: 'archive' | 'updateStatus' | 'addTag' | 'updatePriority', 
    data?: any
  ): Promise<{ success: string[]; failed: string[] }> {
    return handleFirestoreOperation(async () => {
      const batch = writeBatch(db);
      const success: string[] = [];
      const failed: string[] = [];

      for (const chatId of chatIds) {
        const chatRef = doc(chatsCollection, chatId);
        try {
          let updatePayload: Partial<ConsultationMetadata> = {};
          switch (operation) {
            case 'archive':
              updatePayload.status = 'archived';
              break;
            case 'updateStatus':
              if (data?.status) updatePayload.status = data.status;
              break;
            case 'addTag':
              // This needs a transaction or read-then-write for arrayUnion behavior with batch
              // For simplicity, direct update, but be wary of race conditions if not in transaction
              // await updateDoc(chatRef, { 'metadata.tags': arrayUnion(data?.tag) }); 
              // console.warn("Bulk addTag may not be atomic for all tags if run concurrently, consider transaction");
              break;
            case 'updatePriority':
              if (data?.priority) updatePayload.priority = data.priority;
              break;
          }
          if (Object.keys(updatePayload).length > 0) {
             const updateDataForBatch: any = { updatedAt: Timestamp.now(), 'metadata.lastActionDate': Timestamp.now() };
             for (const [key, value] of Object.entries(updatePayload)) {
                updateDataForBatch[`metadata.${key}`] = value;
             }
            batch.update(chatRef, updateDataForBatch);
          }
          success.push(chatId);
        } catch (e) {
          failed.push(chatId);
        }
      }
      await batch.commit();
      return { success, failed };
    }, 'Error in bulk update');
  },

  async searchConsultations(
    userId: string, 
    searchTerm: string, 
    filters?: Partial<Pick<ConsultationMetadata, 'status' | 'priority' | 'category'> & { tags?: string[], dateRange?: { start: Date, end: Date } }>
  ): Promise<Chat[]> {
    return handleFirestoreOperation(async () => {
      let q = query(chatsCollection, where('userId', '==', userId));

      // Basic text search (client-side filtering might be more flexible for complex text search)
      // Firestore doesn't support native full-text search on arbitrary fields easily
      // For more advanced search, consider Algolia or Elasticsearch integration

      if (filters?.status) q = query(q, where('metadata.status', '==', filters.status));
      if (filters?.priority) q = query(q, where('metadata.priority', '==', filters.priority));
      if (filters?.category) q = query(q, where('metadata.category', '==', filters.category));
      if (filters?.tags && filters.tags.length > 0) {
        q = query(q, where('metadata.tags', 'array-contains-any', filters.tags));
      }
      if (filters?.dateRange?.start) {
        q = query(q, where('metadata.lastActionDate', '>=', Timestamp.fromDate(filters.dateRange.start)));
      }
      if (filters?.dateRange?.end) {
        q = query(q, where('metadata.lastActionDate', '<=', Timestamp.fromDate(filters.dateRange.end)));
      }
      
      q = query(q, orderBy('metadata.lastActionDate', 'desc'));

      const querySnapshot = await getDocs(q);
      let results = querySnapshot.docs.map(docToChat);

      // Client-side filter for search term if provided (as Firestore text search is limited)
      if (searchTerm) {
        const lowerSearchTerm = searchTerm.toLowerCase();
        results = results.filter(chat => 
          chat.title.toLowerCase().includes(lowerSearchTerm) ||
          chat.messages.some(msg => msg.text.toLowerCase().includes(lowerSearchTerm))
        );
      }
      return results;
    }, 'Error searching consultations');
  },
};
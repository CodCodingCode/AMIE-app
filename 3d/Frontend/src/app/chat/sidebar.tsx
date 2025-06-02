"use client";
import { cn, truncateText, formatDate, dispatchCustomEvent } from "@/app/lib/utils";
import React, { useState, createContext, useContext, useEffect, useRef, useCallback, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  IconX, IconPlus, IconSettings, IconTrash, IconPin, IconMenu2, IconMessageCircle, 
  IconCalendar, IconFileText, IconPinned, IconUserCircle, IconLogout, IconChevronRight,
  IconAlertTriangle, IconArchive, IconEdit, IconShare, IconCopy, IconExternalLink
} from "@tabler/icons-react";
import { useAuth, AuthButton } from "./Auth";
import { chatService, Chat, ConsultationMetadata } from "./chatService";
import { useRouter, usePathname, useSearchParams } from "next/navigation";
import Image from "next/image";
import { useGlobalFunctions } from "@/app/lib/hooks";

declare global {
  interface Window {
    createNewChat?: () => Promise<void>;
    loadChat?: (chatId: string) => Promise<void>;
    refreshChatList?: () => void;
    deleteChat?: (chatId: string) => Promise<void>;
    // Removed deleteCurrentChat and cleanupEmptyChats as they are handled internally or less used globally
  }
}

// Sidebar Context
interface SidebarContextProps {
  isOpen: boolean;
  setIsOpen: React.Dispatch<React.SetStateAction<boolean>>;
  isPinned: boolean;
  setIsPinned: React.Dispatch<React.SetStateAction<boolean>>;
  activeChatId: string | null;
  setActiveChatId: (id: string | null) => void;
}
const SidebarContext = createContext<SidebarContextProps | undefined>(undefined);
export const useSidebarContext = () => {
  const context = useContext(SidebarContext);
  if (!context) throw new Error("useSidebarContext must be used within SidebarProvider");
  return context;
};

// Sidebar Provider
export const SidebarProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [isPinned, setIsPinned] = useState(false);
  const [activeChatId, setActiveChatId] = useState<string | null>(null);
  return (
    <SidebarContext.Provider value={{ isOpen, setIsOpen, isPinned, setIsPinned, activeChatId, setActiveChatId }}>
      {children}
    </SidebarContext.Provider>
  );
};

// Main Sidebar Component
export const Sidebar: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <SidebarProvider>{children}</SidebarProvider>
);

// Sidebar Body (handles desktop/mobile layout)
export const SidebarBody: React.FC<{ children: React.ReactNode } & React.ComponentProps<typeof motion.div>> = ({ children, ...props }) => (
  <>
    <DesktopSidebar {...props}>{children}</DesktopSidebar>
    <MobileSidebar {...(props as React.ComponentProps<'div'>)}>{children}</MobileSidebar>
  </>
);

// Desktop Sidebar Logic
const DesktopSidebar: React.FC<any> = ({ className, children, ...props }) => {
  const { isOpen, setIsOpen, isPinned, setIsPinned } = useSidebarContext();
  const hoverTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const handleMouseEnter = useCallback(() => {
    if (hoverTimeoutRef.current) clearTimeout(hoverTimeoutRef.current);
    if (!isPinned) setIsOpen(true);
  }, [isPinned, setIsOpen]);

  const handleMouseLeave = useCallback(() => {
    if (!isPinned) {
      hoverTimeoutRef.current = setTimeout(() => setIsOpen(false), 200);
    }
  }, [isPinned, setIsOpen]);

  const togglePin = useCallback(() => {
    setIsPinned(prev => !prev);
    if (!isPinned) setIsOpen(true); // Ensure it stays open when pinned
     if (hoverTimeoutRef.current) clearTimeout(hoverTimeoutRef.current);
  }, [isPinned, setIsPinned, setIsOpen]);

  return (
    <motion.div
      className={cn(
        "h-full hidden md:flex md:flex-col bg-neutral-900/90 backdrop-blur-md border-r border-neutral-700/60 shadow-xl relative",
        className
      )}
      animate={{ width: isOpen ? 280 : 72 }}
      transition={{ duration: 0.25, ease: "easeInOut" }}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      {...props}
    >
      <div className="flex-1 flex flex-col overflow-y-auto no-scrollbar">{children}</div>
      {isOpen && (
        <motion.button
          onClick={togglePin}
          className={cn(
            "absolute top-3 right-3 w-8 h-8 rounded-md flex items-center justify-center transition-all text-neutral-400 hover:text-neutral-100",
            isPinned ? "bg-neutral-700/70 hover:bg-neutral-600/80" : "bg-neutral-800/50 hover:bg-neutral-700/70"
          )}
          initial={{ opacity: 0, scale: 0.7 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.7 }}
          title={isPinned ? "Unpin sidebar" : "Pin sidebar"}
        >
          {isPinned ? <IconPinned size={18} /> : <IconPin size={18} />}
        </motion.button>
      )}
    </motion.div>
  );
};

// Mobile Sidebar Logic
const MobileSidebar: React.FC<any> = ({ className, children, ...props }) => {
  const { isOpen, setIsOpen } = useSidebarContext();
  return (
    <>
      <div className={cn("h-16 flex items-center justify-between md:hidden px-4 bg-neutral-900 border-b border-neutral-700/60 w-full sticky top-0 z-40", className)} {...props}>
        <Logo /> {/* Show compact logo on mobile nav bar */}
        <button onClick={() => setIsOpen(prev => !prev)} className="p-2 text-neutral-200 hover:text-white">
          <IconMenu2 size={24} />
        </button>
      </div>
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ x: '-100%' }}
            animate={{ x: 0 }}
            exit={{ x: '-100%' }}
            transition={{ duration: 0.3, ease: "easeInOut" }}
            className="fixed inset-0 z-50 bg-neutral-900/95 backdrop-blur-lg p-4 flex flex-col md:hidden"
          >
            <div className="flex justify-between items-center mb-6">
              <Logo /> {/* Show full logo inside expanded mobile menu */}
              <button onClick={() => setIsOpen(false)} className="p-2 text-neutral-200 hover:text-white">
                <IconX size={24} />
              </button>
            </div>
            <div className="flex-1 overflow-y-auto no-scrollbar">{children}</div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
};

// Logo Component
export const Logo: React.FC<{ compact?: boolean }> = ({ compact = false }) => {
  const { isOpen } = useSidebarContext();
  const router = useRouter();
  const showText = isOpen || compact === false; // In full sidebar, text depends on isOpen. In compact (mobile nav), always show text.

  return (
    <div 
      className="flex items-center h-16 px-1 cursor-pointer group"
      onClick={() => router.push('/')}
    >
      <Image src="/reallogo.png" alt="Bluebox Logo" width={36} height={36} className="flex-shrink-0 rounded-md" />
      <AnimatePresence>
        {showText && (
            <motion.span
            initial={{ opacity: 0, x: -10, width: 0 }}
            animate={{ opacity: 1, x: 0, width: 'auto' }}
            exit={{ opacity: 0, x: -10, width: 0 }}
            transition={{ duration: 0.2, ease: "easeInOut" }}
            className="ml-2.5 text-xl font-semibold text-white whitespace-nowrap overflow-hidden"
            >
            Bluebox
            </motion.span>
        )}
      </AnimatePresence>
    </div>
  );
};

// Generic Sidebar Item
const SidebarItem: React.FC<{
  icon: React.ElementType;
  text: string;
  onClick?: () => void;
  active?: boolean;
  isNew?: boolean;
  className?: string;
  endContent?: React.ReactNode;
}> = ({ icon: Icon, text, onClick, active, isNew, className, endContent }) => {
  const { isOpen } = useSidebarContext();
  return (
    <motion.div
      onClick={onClick}
      className={cn(
        "group flex items-center h-10 px-3 cursor-pointer rounded-lg mx-2 my-0.5 transition-all duration-150 ease-in-out",
        active ? "bg-blue-600/20 text-blue-300 border border-blue-500/30" : "text-neutral-400 hover:bg-neutral-700/60 hover:text-neutral-200",
        className
      )}
      whileTap={{ scale: 0.97 }}
    >
      <Icon size={isOpen ? 20 : 24} className={cn("flex-shrink-0 transition-all", isOpen ? "mr-3" : "mx-auto")} />
      <AnimatePresence>
        {isOpen && (
          <motion.span 
            initial={{ opacity: 0, x: -5 }} 
            animate={{ opacity: 1, x: 0 }} 
            exit={{ opacity: 0, x: -5 }} 
            transition={{ duration: 0.15 }}
            className="text-sm font-medium truncate flex-1"
          >
            {text}
          </motion.span>
        )}
      </AnimatePresence>
      {isOpen && isNew && <span className="ml-auto text-xs bg-green-500/20 text-green-400 px-1.5 py-0.5 rounded-full">New</span>}
      {isOpen && endContent}
    </motion.div>
  );
};

// Sidebar Section
const SidebarSection: React.FC<{ title?: string; children: React.ReactNode; className?: string }> = ({ title, children, className }) => {
  const { isOpen } = useSidebarContext();
  return (
    <div className={cn("py-2", className)}>
      {isOpen && title && (
        <h3 className="px-4 pt-2 pb-1 text-xs font-semibold text-neutral-500 uppercase tracking-wider">
          {title}
        </h3>
      )}
      {!isOpen && title && <hr className="border-t border-neutral-700/60 mx-3 my-2" />} 
      <div>{children}</div>
    </div>
  );
};

// Chat Item for chat list
const ChatItem: React.FC<{ chat: Chat; onClick: () => void; onDelete: (e: React.MouseEvent) => void; isActive?: boolean }> = 
  ({ chat, onClick, onDelete, isActive }) => {
  const { isOpen } = useSidebarContext();
  const [showDelete, setShowDelete] = useState(false);

  return (
    <SidebarItem
      icon={IconMessageCircle}
      text={truncateText(chat.title || 'New Chat', isOpen ? 25 : 15)}
      onClick={onClick}
      active={isActive}
      endContent={isOpen && (
        <motion.button
          initial={{ opacity: 0}} animate={{opacity:1}} exit={{opacity:0}}
          onClick={(e) => { e.stopPropagation(); onDelete(e); }}
          className="p-1 rounded text-neutral-500 hover:text-red-400 hover:bg-red-500/10 opacity-60 hover:opacity-100 ml-auto"
          title="Delete chat"
          onMouseEnter={() => setShowDelete(true)}
          onMouseLeave={() => setShowDelete(false)}
        >
          <IconTrash size={16} />
        </motion.button>
      )}
    >
      {isOpen && (
        <div className="text-xs text-neutral-500 group-hover:text-neutral-400 mt-0.5">
          {formatDate(chat.updatedAt)}
        </div>
      )}
    </SidebarItem>
  );
};

// Confirmation Dialog
const ConfirmationDialog: React.FC<{
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
}> = ({ isOpen, onClose, onConfirm, title, message, confirmText="Confirm", cancelText="Cancel" }) => (
  <AnimatePresence>
    {isOpen && (
      <motion.div 
        initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black/50 z-[100] flex items-center justify-center p-4"
        onClick={onClose}
      >
        <motion.div 
          initial={{ scale: 0.9, opacity: 0}} 
          animate={{ scale: 1, opacity: 1}} 
          exit={{ scale: 0.9, opacity: 0}}
          onClick={(e) => e.stopPropagation()}
          className="bg-neutral-800 rounded-xl p-6 shadow-2xl w-full max-w-sm border border-neutral-700"
        >
          <div className="flex items-center mb-3">
            <IconAlertTriangle className="text-yellow-400 mr-3" size={24}/>
            <h2 className="text-lg font-semibold text-white">{title}</h2>
          </div>
          <p className="text-sm text-neutral-300 mb-6">{message}</p>
          <div className="flex justify-end space-x-3">
            <button 
              onClick={onClose} 
              className="px-4 py-2 rounded-md text-sm font-medium text-neutral-300 bg-neutral-700 hover:bg-neutral-600 transition-colors"
            >
              {cancelText}
            </button>
            <button 
              onClick={() => { onConfirm(); onClose(); }}
              className="px-4 py-2 rounded-md text-sm font-medium text-white bg-red-600 hover:bg-red-700 transition-colors"
            >
              {confirmText}
            </button>
          </div>
        </motion.div>
      </motion.div>
    )}
  </AnimatePresence>
);

// Main Sidebar Menu structure
export const SidebarMenu = () => {
  const { user, loading: authLoading, logOut } = useAuth();
  const { isOpen, setIsOpen, activeChatId, setActiveChatId } = useSidebarContext();
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const [chats, setChats] = useState<Chat[]>([]);
  const [isLoadingChats, setIsLoadingChats] = useState(true);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [chatToDelete, setChatToDelete] = useState<string | null>(null);

  const loadChats = useCallback(async () => {
    if (!user) {
      setChats([]);
      setIsLoadingChats(false);
      return;
    }
    setIsLoadingChats(true);
    try {
      const userChats = await chatService.getUserChats(user);
      setChats(userChats);
    } catch (error) {
      console.error("Failed to load chats:", error);
      // Optionally, show error to user
    } finally {
      setIsLoadingChats(false);
    }
  }, [user]);

  useEffect(() => {
    loadChats();
    const currentUrlChatId = searchParams.get('id');
    if (currentUrlChatId) {
        setActiveChatId(currentUrlChatId);
    }
  }, [user, loadChats, searchParams, setActiveChatId]);

  // Event listeners for global chat actions
  useEffect(() => {
    const handleRefresh = () => loadChats();
    const handleChatUpdate = (event: Event) => {
      const customEvent = event as CustomEvent<{ chatId: string | null }>;
      setActiveChatId(customEvent.detail.chatId);
      // If a chat was created or updated, refresh the list
      if (customEvent.detail.chatId) loadChats(); 
    };

    window.addEventListener('refreshChatList', handleRefresh);
    window.addEventListener('currentChatUpdate', handleChatUpdate);
    return () => {
      window.removeEventListener('refreshChatList', handleRefresh);
      window.removeEventListener('currentChatUpdate', handleChatUpdate);
    };
  }, [loadChats, setActiveChatId]);

  const handleNewChat = async () => {
    if (!window.createNewChat) return;
    await window.createNewChat(); // Calls function exposed by ChatWindow
    if (!isOpen) setIsOpen(true); // Open sidebar if closed
  };

  const handleChatClick = (chatId: string) => {
    setActiveChatId(chatId);
    router.push(`/chat?id=${chatId}`); // Update URL
    if (window.loadChat) window.loadChat(chatId); // Ensure ChatWindow loads it
    if (isOpen && window.innerWidth < 768) setIsOpen(false); // Close mobile sidebar on nav
  };

  const handleDeleteChat = (chatId: string) => {
    setChatToDelete(chatId);
    setShowDeleteDialog(true);
  };

  const confirmDeleteChat = async () => {
    if (!chatToDelete || !user) return;
    try {
      await chatService.deleteChat(chatToDelete);
      setChats(prev => prev.filter(c => c.id !== chatToDelete));
      if (activeChatId === chatToDelete) {
        setActiveChatId(null);
        router.push('/chat'); // Navigate to new chat if active one was deleted
        if (window.createNewChat) window.createNewChat(); // Start a new chat implicitly
      }
    } catch (error) {
      console.error("Failed to delete chat:", error);
    }
    setChatToDelete(null);
  };

  const handleSignOut = async () => {
    await logOut();
    router.push('/'); // Redirect to home or login page after sign out
    setChats([]);
    setActiveChatId(null);
  };

  const mainNavigationItems = [
    // { icon: IconLayoutDashboard, text: 'Dashboard', onClick: () => router.push('/dashboard'), active: pathname === '/dashboard' },
    { icon: IconMessageCircle, text: 'New Chat', onClick: handleNewChat, isNew: true },
    { icon: IconArchive, text: 'Consultations', onClick: () => router.push('/consultations'), active: pathname === '/consultations' },
  ];

  const settingsNavigationItems = [
    { icon: IconSettings, text: 'Settings', onClick: () => router.push('/settings'), active: pathname === '/settings' },
  ];

  return (
    <div className="flex flex-col h-full">
      <Logo />
      <SidebarSection className="flex-grow overflow-y-auto no-scrollbar">
        <SidebarItem 
            icon={IconPlus}
            text="New Consultation"
            onClick={handleNewChat}
            className="bg-blue-600/80 text-white hover:bg-blue-500/80 my-2 font-semibold"
        />
        <SidebarSection title="Recent Chats">
          {isLoadingChats && isOpen && <p className="px-4 text-xs text-neutral-500">Loading chats...</p>}
          {!isLoadingChats && chats.length === 0 && isOpen && <p className="px-4 text-xs text-neutral-500">No recent chats.</p>}
          <AnimatePresence>
            {chats.map(chat => (
              <ChatItem 
                key={chat.id} 
                chat={chat} 
                onClick={() => handleChatClick(chat.id)} 
                onDelete={(e) => { e.stopPropagation(); handleDeleteChat(chat.id); }}
                isActive={chat.id === activeChatId} 
              />
            ))}
          </AnimatePresence>
        </SidebarSection>
      </SidebarSection>

      {/* User/Auth Section */}
      <SidebarSection className="mt-auto border-t border-neutral-700/60 pt-2 pb-1">
        {user ? (
          <div className={cn("px-2", isOpen ? "py-2" : "py-3")} >
            <div className="flex items-center justify-between">
              {isOpen && (
                <div className="flex items-center min-w-0">
                  <IconUserCircle size={28} className="text-neutral-400 flex-shrink-0" />
                  <div className="ml-2.5 min-w-0">
                    <p className="text-sm font-medium text-neutral-200 truncate">{user.displayName || 'User'}</p>
                    <p className="text-xs text-neutral-500 truncate">{user.email}</p>
                  </div>
                </div>
              )}
               <button 
                  onClick={handleSignOut}
                  className={cn(
                    "p-2 rounded-md text-neutral-400 hover:text-red-400 hover:bg-red-500/10 transition-colors",
                    !isOpen && "w-full flex justify-center"
                  )}
                  title="Sign Out"
                >
                  <IconLogout size={isOpen ? 20 : 22} />
                </button>
            </div>
          </div>
        ) : (
          <div className="p-3">
            <AuthButton />
          </div>
        )}
      </SidebarSection>

      <ConfirmationDialog 
        isOpen={showDeleteDialog}
        onClose={() => setShowDeleteDialog(false)}
        onConfirm={confirmDeleteChat}
        title="Delete Chat?"
        message="Are you sure you want to delete this chat? This action cannot be undone."
        confirmText="Delete"
      />
    </div>
  );
};
"use client";
import { cn } from "@/app/lib/utils";
import React, { useState, createContext, useContext, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { 
  IconX, 
  IconPlus, 
  IconSettings, 
  IconTrash,
  IconPin,
  IconMenu2,
  IconMessageCircle,
  IconCalendar,
  IconFileText,
  IconPinned
} from "@tabler/icons-react";
import { useAuth } from "./Auth";
import { chatService, Chat } from "./chatService";
import { useRouter } from "next/navigation";
import Image from "next/image";

declare global {
  interface Window {
    createNewChat?: () => void;
    loadChat?: (chatId: string) => void;
    refreshChatList?: () => void;
    deleteCurrentChat?: () => void;
    deleteChat?: (chatId: string) => void;
    cleanupEmptyChats?: () => void;
  }
}

interface SidebarContextProps {
  open: boolean;
  setOpen: React.Dispatch<React.SetStateAction<boolean>>;
  isPinned: boolean;
  setIsPinned: React.Dispatch<React.SetStateAction<boolean>>;
}

const SidebarContext = createContext<SidebarContextProps | undefined>(undefined);

export const useSidebar = () => {
  const context = useContext(SidebarContext);
  if (!context) throw new Error("useSidebar must be used within SidebarProvider");
  return context;
};

export const SidebarProvider = ({ children, open: openProp, setOpen: setOpenProp }: {
  children: React.ReactNode;
  open?: boolean;
  setOpen?: React.Dispatch<React.SetStateAction<boolean>>;
}) => {
  const [stateOpen, setStateOpen] = useState(false);
  const [isPinned, setIsPinned] = useState(false);
  const open = openProp ?? stateOpen;
  const setOpen = setOpenProp ?? setStateOpen;
  return (
    <SidebarContext.Provider value={{ open, setOpen, isPinned, setIsPinned }}>
      {children}
    </SidebarContext.Provider>
  );
};

export const Sidebar = ({ children, open, setOpen }: {
  children: React.ReactNode;
  open?: boolean;
  setOpen?: React.Dispatch<React.SetStateAction<boolean>>;
}) => <SidebarProvider open={open} setOpen={setOpen}>{children}</SidebarProvider>;

export const SidebarBody = ({ children, ...props }: { children: React.ReactNode } & React.ComponentProps<typeof motion.div>) => (
  <>
    <DesktopSidebar {...props}>{children}</DesktopSidebar>
    <MobileSidebar {...(props as React.ComponentProps<'div'>)}>{children}</MobileSidebar>
  </>
);

export const DesktopSidebar = ({ className, children, ...props }: {
  className?: string;
  children: React.ReactNode;
} & Omit<React.ComponentProps<typeof motion.div>, 'children'>) => {
  const { open, setOpen, isPinned, setIsPinned } = useSidebar();
  const hoverRef = useRef<NodeJS.Timeout | null>(null);
  
  const handleMouseEnter = () => {
    if (hoverRef.current) {
      clearTimeout(hoverRef.current);
    }
    if (!isPinned) {
      setOpen(true);
    }
  };

  const handleMouseLeave = () => {
    if (!isPinned) {
      hoverRef.current = setTimeout(() => setOpen(false), 300);
    }
  };

  const handlePinToggle = () => {
    if (isPinned) {
      setIsPinned(false);
    } else {
      setIsPinned(true);
      setOpen(true);
      if (hoverRef.current) {
        clearTimeout(hoverRef.current);
      }
    }
  };

  return (
    <>
      <motion.div
        className={cn(
          "h-full hidden md:flex md:flex-col bg-slate-900/95 backdrop-blur-sm border-r border-slate-700/50 z-10 no-scrollbar shadow-lg relative", 
          className
        )}
        style={{ pointerEvents: 'auto' }}
        animate={{ width: open ? 260 : 68 }}
        transition={{ duration: 0.3, ease: [0.4, 0, 0.2, 1] }}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
        {...props}
      >
        {/* Remove the logo section from here */}
        
        {/* Main Content */}
        <div className="flex-1 flex flex-col">
          {children}
        </div>
        
        {/* Pin/Unpin Button - Only show when sidebar is open */}
        <AnimatePresence>
          {open && (
            <motion.button
              onClick={handlePinToggle}
              className={cn(
                "absolute top-4 right-4 w-8 h-8 rounded-lg flex items-center justify-center transition-colors z-20",
                isPinned 
                  ? "bg-blue-600/20 text-blue-400 hover:bg-blue-600/30 border border-blue-500/30" 
                  : "bg-slate-800/60 text-slate-400 hover:bg-slate-700 hover:text-slate-200"
              )}
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.8 }}
              transition={{ duration: 0.2 }}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              title={isPinned ? "Unpin sidebar (will close on mouse leave)" : "Pin sidebar (keep open)"}
            >
              {isPinned ? (
                <IconPinned className="w-4 h-4" />
              ) : (
                <IconPin className="w-4 h-4" />
              )}
            </motion.button>
          )}
        </AnimatePresence>
      </motion.div>
    </>
  );
};

export const MobileSidebar = ({ className, children, ...props }: React.ComponentProps<'div'>) => {
  const { open, setOpen } = useSidebar();
  return (
    <div className={cn("h-14 flex items-center justify-between md:hidden px-4 bg-slate-900/95 backdrop-blur-sm border-b border-slate-700/50 w-full", className)} {...props}>
      <IconMenu2 onClick={() => setOpen(!open)} className="text-slate-200 hover:text-white transition-colors cursor-pointer" size={20} />
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ x: '-100%', opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: '-100%', opacity: 0 }}
            transition={{ duration: 0.3, ease: [0.4, 0, 0.2, 1] }}
            className="fixed inset-0 z-50 bg-slate-900/98 backdrop-blur-md p-6 flex flex-col"
          >
            <div className="flex justify-end mb-6">
              <IconX 
                onClick={() => setOpen(false)} 
                className="text-slate-200 hover:text-white transition-colors cursor-pointer" 
                size={24} 
              />
            </div>
            {children}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export const Logo = () => {
  const { open } = useSidebar();
  const router = useRouter();

  return (
    <div className="flex items-center px-4 h-16 border-b border-slate-700/30">
      <div 
        className="flex items-center cursor-pointer" 
        onClick={() => router.push('/')}
      >
        <div className="relative flex-shrink-0">
          <Image 
            src="/reallogo.png" 
            alt="Bluebox" 
            width={32} 
            height={32} 
            className="flex-shrink-0"
          />
        </div>
        <div className="overflow-hidden ml-3">
          <motion.div
            initial={false}
            animate={{ 
              opacity: open ? 1 : 0,
              x: open ? 0 : -10,
              width: open ? 'auto' : 0
            }}
            transition={{ duration: 0.2 }}
            className="text-white font-semibold text-lg whitespace-nowrap"
          >
            Bluebox
          </motion.div>
        </div>
      </div>
    </div>
  );
};

const SidebarItem = ({ 
  icon: Icon, 
  text,
  onClick,
  active = false,
  isNew = false
}: { 
  icon: React.FC<{ className?: string; size?: number }>;
  text: string; 
  onClick?: () => void;
  active?: boolean;
  isNew?: boolean;
}) => {
  const { open } = useSidebar();
  
  return (
    <div 
      className={cn(
        "group flex items-center h-11 px-3 cursor-pointer rounded-lg mx-2 transition-all duration-200 relative",
        active 
          ? "bg-gradient-to-r from-blue-600/20 to-blue-500/10 text-blue-400 shadow-sm border border-blue-500/20" 
          : "hover:bg-slate-800/60 text-slate-300 hover:text-white"
      )}
      onClick={onClick}
    >
      <div className="flex items-center gap-3 w-full min-w-0">
        <div className={cn(
          "flex-shrink-0 transition-colors",
          active ? "text-blue-400" : "text-slate-400 group-hover:text-slate-200"
        )}>
          <Icon size={18} />
        </div>
        <div className="overflow-hidden flex-1">
          <motion.div
            initial={false}
            animate={{ 
              opacity: open ? 1 : 0,
              width: open ? 'auto' : 0
            }}
            transition={{ duration: 0.2 }}
            className="min-w-0"
          >
            <span className={cn(
              "text-sm font-medium whitespace-nowrap block truncate",
              active ? "text-blue-400" : "text-slate-300 group-hover:text-white"
            )}>
              {text}
            </span>
          </motion.div>
        </div>
        {isNew && (
          <div className="overflow-hidden">
            <motion.div 
              initial={false}
              animate={{ 
                opacity: open ? 1 : 0,
                scale: open ? 1 : 0.8
              }}
              transition={{ duration: 0.2 }}
              className="flex-shrink-0"
            >
              <IconPlus 
                size={14} 
                className={cn(
                  "transition-colors",
                  active ? "text-blue-400" : "text-slate-500 group-hover:text-slate-300"
                )} 
              />
            </motion.div>
          </div>
        )}
      </div>
    </div>
  );
};

const SidebarSection = ({ title, children }: { title?: string; children: React.ReactNode }) => {
  const { open } = useSidebar();
  
  return (
    <div className="mt-6">
      {title && (
        <div className="overflow-hidden">
          <motion.div
            initial={false}
            animate={{ 
              opacity: open ? 1 : 0,
              height: open ? 'auto' : 0
            }}
            transition={{ duration: 0.2 }}
            className="px-5 py-2 text-xs text-slate-500 uppercase font-semibold tracking-wider"
          >
            {title}
          </motion.div>
        </div>
      )}
      <div className="mt-2 flex flex-col gap-1">
        {children}
      </div>
    </div>
  );
};

const ChatItem = ({ 
  chat, 
  onClick, 
  onDelete, 
  isActive = false 
}: { 
  chat: Chat; 
  onClick: () => void; 
  onDelete: (e: React.MouseEvent) => void;
  isActive?: boolean;
}) => {
  const { open } = useSidebar();
  
  return (
    <div
      className={cn(
        "group flex items-center justify-between h-10 px-3 cursor-pointer rounded-lg mx-2 transition-all duration-200",
        isActive 
          ? "bg-gradient-to-r from-blue-600/15 to-blue-500/5 border border-blue-500/20" 
          : "hover:bg-slate-800/50"
      )}
    >
      <div
        className="flex-1 flex items-center h-full min-w-0"
        onClick={onClick}
      >
        <div className="flex items-center gap-3 w-full min-w-0">
          <div className="overflow-hidden flex-1">
            <motion.div
              initial={false}
              animate={{ 
                opacity: open ? 1 : 0,
                width: open ? 'auto' : 0
              }}
              transition={{ duration: 0.2 }}
              className="min-w-0"
            >
              <span 
                className={cn(
                  "text-sm block truncate max-w-[180px] transition-colors",
                  isActive ? "text-blue-300" : "text-slate-300 group-hover:text-white"
                )}
                title={chat.title || "New Chat"}
              >
                {chat.title || "New Chat"}
              </span>
            </motion.div>
          </div>
        </div>
      </div>
      <div className="overflow-hidden">
        <motion.div
          initial={false}
          animate={{
            opacity: open ? 0 : 0,
            scale: open ? 1 : 0.8
          }}
          whileHover={{ opacity: 1, scale: 1.1 }}
          transition={{ duration: 0.15 }}
          className="flex-shrink-0 ml-2 p-1 rounded-md hover:bg-red-500/20 group-hover:opacity-100"
          onClick={onDelete}
        >
          <IconTrash className="h-3.5 w-3.5 text-slate-400 hover:text-red-400 transition-colors" />
        </motion.div>
      </div>
    </div>
  );
};

export const SidebarMenu = () => {
  const { user } = useAuth();
  const { open } = useSidebar();
  const router = useRouter();
  const [chats, setChats] = useState<Chat[]>([]);
  const [loading, setLoading] = useState(false);
  const [currentMessages, setCurrentMessages] = useState<number>(0);
  const [currentChatId, setCurrentChatId] = useState<string | null>(null);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [chatToDelete, setChatToDelete] = useState<string | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);


  useEffect(() => {
    if (!user) return;
    setLoading(true);
    
    // Clean up empty chats when user logs in, then load chats
    const loadChats = async () => {
      try {
        await chatService.cleanupEmptyChats(user);
        const userChats = await chatService.getUserChats(user);
        setChats(userChats);
      } catch (error) {
        console.error('Error loading chats:', error);
        // Fallback to just loading chats without cleanup
        const userChats = await chatService.getUserChats(user);
        setChats(userChats);
      } finally {
        setLoading(false);
      }
    };
    
    loadChats();
  }, [user]);

  // Listen for refresh events to update chat list
  useEffect(() => {
    const handleRefreshChatList = async () => {
      if (!user) return;
      setLoading(true);
      try {
        const updatedChats = await chatService.getUserChats(user);
        setChats(updatedChats);
      } catch (error) {
        console.error('Error refreshing chat list:', error);
      } finally {
        setLoading(false);
      }
    };

    if (typeof window !== 'undefined') {
      window.addEventListener('refreshChatList', handleRefreshChatList);
      
      // Create custom event listener to track current message count
      const handleMessageCountUpdate = (event: CustomEvent) => {
        setCurrentMessages(event.detail.count);
      };
      
      // Add listener for current chat ID updates
      const handleCurrentChatUpdate = (event: CustomEvent) => {
        setCurrentChatId(event.detail.chatId);
      };
      
      window.addEventListener('messageCountUpdate', handleMessageCountUpdate as EventListener);
      window.addEventListener('currentChatUpdate', handleCurrentChatUpdate as EventListener);
      
      return () => {
        window.removeEventListener('refreshChatList', handleRefreshChatList);
        window.removeEventListener('messageCountUpdate', handleMessageCountUpdate as EventListener);
        window.removeEventListener('currentChatUpdate', handleCurrentChatUpdate as EventListener);
      };
    }
  }, [user]);

  // Register global functions including the new cleanup function
  useEffect(() => {
    if (typeof window !== 'undefined') {
      // Cleanup function
      window.cleanupEmptyChats = async () => {
        if (!user) return;
        
        try {
          await chatService.cleanupEmptyChats(user);
          // Refresh the chat list after cleanup
          const updatedChats = await chatService.getUserChats(user);
          setChats(updatedChats);
          
          // Dispatch refresh event for other components
          window.dispatchEvent(new CustomEvent('refreshChatList'));
        } catch (error) {
          console.error('Error during cleanup:', error);
        }
      };

      window.deleteChat = (chatId: string) => {
        setChatToDelete(chatId);
        setIsDeleteDialogOpen(true);
      };

      return () => {
        delete window.cleanupEmptyChats;
        delete window.deleteChat;
      };
    }
  }, [user]);

  const handleNewChat = () => {
    // Simply create a new chat when user clicks "New Chat"
    window.createNewChat?.();
  };

  const handleConsultations = () => {
    router.push('/consultations');
  };

  const handleChatClick = (chatId: string) => {
    window.loadChat?.(chatId);
    setCurrentChatId(chatId);
  };

  const handleDeleteClick = (e: React.MouseEvent, chatId: string) => {
    e.stopPropagation(); // Prevent triggering the chat load
    setChatToDelete(chatId);
    setIsDeleteDialogOpen(true);
  };

  const handleCloseDeleteDialog = () => {
    setIsDeleteDialogOpen(false);
    setChatToDelete(null);
  };

  const handleDeleteConfirm = async () => {
    if (!chatToDelete || isDeleting || !user) return;
    
    setIsDeleting(true);
    try {
      await chatService.deleteChat(chatToDelete);
      
      // Update local state
      setChats(prev => prev.filter(chat => chat.id !== chatToDelete));
      
      // If we deleted the current chat, create a new one
      if (chatToDelete === currentChatId) {
        window.createNewChat?.();
      }
      
      // Refresh the chat list in the sidebar
      if (typeof window !== 'undefined') {
        window.dispatchEvent(new CustomEvent('refreshChatList'));
      }
    } catch (error) {
      console.error('Error deleting chat:', error);
    } finally {
      setIsDeleting(false);
      setIsDeleteDialogOpen(false);
      setChatToDelete(null);
    }
  };

  // Filter out empty chats from display (chats with messageCount of 0)
  const displayChats = chats.filter(chat => {
    return chat.messages.length > 0 || chat.id === currentChatId;
  });

  return (
    <SidebarBody className="flex flex-col">
      <div className="flex-1 flex flex-col">
        <Logo />

        {/* Main Navigation */}
        <SidebarSection>
          <SidebarItem
            icon={IconMessageCircle}
            text="New chat"
            onClick={handleNewChat}
            active={false}
            isNew={true}
          />
          <SidebarItem
            icon={IconCalendar}
            text="Manage Consultations"
            onClick={handleConsultations}
          />
          <SidebarItem
            icon={IconFileText}
            text="EHR"
            onClick={() => router.push("/ehr")}
          />
        </SidebarSection>

        {/* Chat History - Removed "Recent Chats" title */}
        <SidebarSection>
          {loading ? (
            <div className="px-5 py-3 text-center">
              <div className="flex items-center justify-center gap-2">
                <div className="w-2 h-2 bg-slate-500 rounded-full animate-pulse"></div>
                <div className="w-2 h-2 bg-slate-500 rounded-full animate-pulse delay-75"></div>
                <div className="w-2 h-2 bg-slate-500 rounded-full animate-pulse delay-150"></div>
              </div>
              <div className="overflow-hidden">
                <motion.span 
                  initial={false}
                  animate={{ 
                    opacity: open ? 1 : 0,
                    height: open ? 'auto' : 0
                  }}
                  transition={{ duration: 0.2 }}
                  className="text-xs text-slate-500 mt-2 block"
                >
                  Loading chats...
                </motion.span>
              </div>
            </div>
          ) : (
            <div className="flex flex-col max-h-[calc(100vh-280px)] overflow-y-auto no-scrollbar">
              {displayChats.slice(0, 15).map((chat) => (
                <ChatItem
                  key={chat.id}
                  chat={chat}
                  onClick={() => handleChatClick(chat.id)}
                  onDelete={(e) => handleDeleteClick(e, chat.id)}
                  isActive={chat.id === currentChatId}
                />
              ))}
              {displayChats.length > 15 && (
                <div
                  className="flex items-center justify-center h-10 px-3 mx-2 text-slate-500 hover:text-slate-300 transition-colors cursor-pointer rounded-lg hover:bg-slate-800/40"
                  onClick={() => router.push('/chat-history')}
                >
                  <div className="flex items-center gap-2">
                    <div className="flex gap-1">
                      <div className="w-1 h-1 rounded-full bg-slate-500"></div>
                      <div className="w-1 h-1 rounded-full bg-slate-500"></div>
                      <div className="w-1 h-1 rounded-full bg-slate-500"></div>
                    </div>
                    <div className="overflow-hidden">
                      <motion.span
                        initial={false}
                        animate={{ 
                          opacity: open ? 1 : 0,
                          width: open ? 'auto' : 0
                        }}
                        transition={{ duration: 0.2 }}
                        className="text-xs font-medium whitespace-nowrap"
                      >
                        {displayChats.length - 15} more chats
                      </motion.span>
                    </div>
                  </div>
                </div>
              )}
              {displayChats.length === 0 && !loading && (
                <div className="px-5 py-6 text-center">
                  <div className="text-slate-500 text-sm">
                    {open ? "No chats yet" : "Empty"}
                  </div>
                  <div className="overflow-hidden">
                    <motion.div 
                      initial={false}
                      animate={{ 
                        opacity: open ? 1 : 0,
                        height: open ? 'auto' : 0
                      }}
                      transition={{ duration: 0.2 }}
                      className="text-xs text-slate-600 mt-1"
                    >
                      Start a conversation to see your chat history
                    </motion.div>
                  </div>
                </div>
              )}
            </div>
          )}
        </SidebarSection>

        {/* Bottom Section */}
        <div className="mt-auto border-t border-slate-700/30 pt-4">
          <SidebarSection>
            {user && (
              <SidebarItem
                icon={IconSettings}
                text="Settings & help"
                onClick={() => router.push("/settings")}
              />
            )}
          </SidebarSection>
        </div>
      </div>

      {/* Enhanced Delete Confirmation Dialog */}
      <AnimatePresence>
        {isDeleteDialogOpen && (
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
          >
            <motion.div 
              initial={{ opacity: 0, scale: 0.9, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.9, y: 20 }}
              transition={{ duration: 0.2 }}
              className="bg-white rounded-xl p-6 max-w-sm mx-4 shadow-2xl border border-gray-200"
            >
              <div className="flex items-start gap-4">
                <div className="flex-shrink-0 w-10 h-10 bg-red-100 rounded-full flex items-center justify-center">
                  <IconTrash className="w-5 h-5 text-red-600" />
                </div>
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">Delete Chat</h3>
                  <p className="text-sm text-gray-600 mb-6">
                    Are you sure you want to delete this chat? This action cannot be undone and all messages will be permanently removed.
                  </p>
                  <div className="flex justify-end space-x-3">
                    <button
                      onClick={handleCloseDeleteDialog}
                      disabled={isDeleting}
                      className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500 transition-colors disabled:opacity-50"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={handleDeleteConfirm}
                      disabled={isDeleting}
                      className={`px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-lg hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 transition-colors ${
                        isDeleting ? "opacity-50 cursor-not-allowed" : ""
                      }`}
                    >
                      {isDeleting ? (
                        <span className="flex items-center gap-2">
                          <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                          Deleting...
                        </span>
                      ) : (
                        "Delete"
                      )}
                    </button>
                  </div>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </SidebarBody>
  );
};
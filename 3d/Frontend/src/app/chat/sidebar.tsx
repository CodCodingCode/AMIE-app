"use client";
import { cn } from "@/app/lib/utils";
import React, { useState, createContext, useContext, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { IconMenu2, IconX, IconPlus, IconSettings, IconEdit, IconDiamond } from "@tabler/icons-react";
import Image from "next/image";
import { useAuth, AuthButton } from "./Auth";
import { chatService, Chat } from "./chatService";
import { useRouter } from "next/navigation";


declare global {
 interface Window {
   createNewChat?: () => void;
   loadChat?: (chatId: string) => void;
   refreshChatList?: () => void;
 }
}


interface SidebarContextProps {
 open: boolean;
 setOpen: React.Dispatch<React.SetStateAction<boolean>>;
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
 const open = openProp ?? stateOpen;
 const setOpen = setOpenProp ?? setStateOpen;
 return <SidebarContext.Provider value={{ open, setOpen }}>{children}</SidebarContext.Provider>;
};


export const Sidebar = ({ children, open, setOpen }: {
 children: React.ReactNode;
 open?: boolean;
 setOpen?: React.Dispatch<React.SetStateAction<boolean>>;
}) => <SidebarProvider open={open} setOpen={setOpen}>{children}</SidebarProvider>;


export const SidebarBody = (props: React.ComponentProps<typeof motion.div>) => (
 <>
   <DesktopSidebar {...props} />
   <MobileSidebar {...(props as React.ComponentProps<'div'>)} />
 </>
);


export const DesktopSidebar = ({ className, children, ...props }: React.ComponentProps<typeof motion.div>) => {
 const { open, setOpen } = useSidebar();
 const hoverRef = useRef<NodeJS.Timeout | null>(null);
 return (
   <motion.div
     className={cn("h-full hidden md:flex md:flex-col bg-white border-r border-mountbattenPink z-10 no-scrollbar", className)}
     style={{ pointerEvents: 'auto' }}
     animate={{ width: open ? 250 : 80 }}
     transition={{ duration: 0.2, ease: 'easeInOut' }}
     onMouseEnter={() => { hoverRef.current && clearTimeout(hoverRef.current); setOpen(true); }}
     onMouseLeave={() => { hoverRef.current = setTimeout(() => setOpen(false), 300); }}
     {...props}
   >
     {children}
   </motion.div>
 );
};


export const MobileSidebar = ({ className, children, ...props }: React.ComponentProps<'div'>) => {
 const { open, setOpen } = useSidebar();
 return (
   <div className={cn("h-10 flex items-center justify-between md:hidden px-4 py-4 bg-white w-full", className)} {...props}>
     <IconMenu2 onClick={() => setOpen(!open)} className="text-dukeBlue" />
     <AnimatePresence>
       {open && (
         <motion.div
           initial={{ x: '-100%', opacity: 0 }}
           animate={{ x: 0, opacity: 1 }}
           exit={{ x: '-100%', opacity: 0 }}
           transition={{ duration: 0.3 }}
           className="fixed inset-0 z-50 bg-white p-10 flex flex-col justify-between"
         >
           <IconX onClick={() => setOpen(false)} className="absolute top-4 right-4 text-dukeBlue" />
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
   <div className="flex items-center px-5 h-16">
     <div className="flex items-center gap-3">
       <div onClick={() => router.push('/')} className="cursor-pointer">
         <Image src="/reallogo.png" alt="Bluebox" width={32} height={32} />
       </div>
     </div>
   </div>
 );
};


const SidebarItem = ({
 icon: Icon,
 text,
 onClick,
 active = false
}: {
 icon: React.FC<{ className?: string }>;
 text: string;
 onClick?: () => void;
 active?: boolean;
}) => {
 const { open } = useSidebar();
  return (
   <div
     className={cn(
       "flex items-center h-10 px-5 cursor-pointer rounded-md mx-2",
       active ? "bg-trueBlue text-dukeBlue" : "hover:bg-trueBlue"
     )}
     onClick={onClick}
   >
     <div className="flex items-center gap-5">
       <Icon className={cn("h-5 w-5", active ? "text-dukeBlue" : "text-mountbattenPink")} />
       <AnimatePresence>
         {open && (
           <motion.span
             initial={{ opacity: 0 }}
             animate={{ opacity: 1 }}
             exit={{ opacity: 0 }}
             transition={{ duration: 0.2 }}
             className={cn("text-sm whitespace-nowrap", active ? "text-dukeBlue" : "text-mountbattenPink")}
           >
             {text}
           </motion.span>
         )}
       </AnimatePresence>
     </div>
   </div>
 );
};


const SidebarSection = ({ title, children }: { title?: string; children: React.ReactNode }) => {
 const { open } = useSidebar();
  return (
   <div className="mt-5">
     {title && open && (
       <div className="px-7 py-1 text-xs text-mountbattenPink uppercase">
         {title}
       </div>
     )}
     <div className="mt-1 flex flex-col gap-1">
       {children}
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


 useEffect(() => {
   if (!user) return;
   setLoading(true);
   chatService.getUserChats(user).then(setChats).finally(() => setLoading(false));
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
    
     window.addEventListener('messageCountUpdate', handleMessageCountUpdate as EventListener);
    
     return () => {
       window.removeEventListener('refreshChatList', handleRefreshChatList);
       window.removeEventListener('messageCountUpdate', handleMessageCountUpdate as EventListener);
     };
   }
 }, [user]);


 const handleNewChat = () => {
   // Only trigger new chat if we have messages in the current chat
   if (currentMessages > 0) {
     window.createNewChat?.();
   }
 };


 const handleConsultations = () => {
   router.push('/consultations')
 }


 return (
   <SidebarBody className="flex flex-col">
     <div className="flex-1 flex flex-col">
       <Logo />
      
       <SidebarSection>
         <SidebarItem
           icon={IconEdit}
           text="New chat"
           onClick={handleNewChat}
           active={currentMessages === 0} // Highlight when we're already in a new chat
         />
       </SidebarSection>
      
       <SidebarSection >
         {loading ? (
           <div className={cn(
             "px-7 py-2 text-sm text-mountbattenPink",
             !open && "text-center"
           )}>
             {open ? "Loading..." : "..."}
           </div>
         ) : (
           <div className="flex flex-col overflow-y-auto max-h-[calc(100vh-220px)] no-scrollbar">
             {chats.map(chat => (
               <div
                 key={chat.id}
                 onClick={() => window.loadChat?.(chat.id)}
                 className="flex items-center h-10 px-5 cursor-pointer hover:bg-trueBlue rounded-md mx-2"
               >
                 <AnimatePresence>
                   {open && (
                     <motion.span
                       initial={{ opacity: 0 }}
                       animate={{ opacity: 1 }}
                       exit={{ opacity: 0 }}
                       transition={{ duration: 0.2 }}
                       className="truncate max-w-[240px] text-sm text-mountbattenPink"
                     >
                       {chat.title || "New Chat"}
                     </motion.span>
                   )}
                   {!open && (
                     <div className="w-5 h-5 flex items-center justify-center">
                       <div className="w-2 h-2 rounded-full bg-mountbattenPink"></div>
                     </div>
                   )}
                 </AnimatePresence>
               </div>
             ))}
           </div>
         )}
       </SidebarSection>
       <SidebarSection>
         <SidebarItem
           icon={IconEdit}
           text="Manage Consultations"
           onClick={handleConsultations}
         />
       </SidebarSection>
       <SidebarSection>
         <SidebarItem
           icon={IconEdit}
           text="EHR"
           onClick={() => router.push('/ehr')}
         />
         {user ? (
           <SidebarItem
             icon={IconSettings}
             text="Settings & help"
             onClick={() => router.push('/settings')}
           />
         ) : null}
       </SidebarSection>
     </div>
   </SidebarBody>
 );
};


"use client";
import { cn } from "../lib/utils";
import React, { useState, createContext, useContext } from "react";
import { AnimatePresence, motion } from "motion/react";
import { IconBrandTabler, IconMenu2, IconUserBolt, IconX } from "@tabler/icons-react";
import Image from "next/image";

interface Links {
  label: string;
  href: string;
  icon: React.JSX.Element | React.ReactNode;
}

interface SidebarContextProps {
  open: boolean;
  setOpen: React.Dispatch<React.SetStateAction<boolean>>;
}

const SidebarContext = createContext<SidebarContextProps | undefined>(undefined);

export const useSidebar = () => {
  const context = useContext(SidebarContext);
  if (!context) {
    throw new Error("useSidebar must be used within a SidebarProvider");
  }
  return context;
};

export const SidebarProvider = ({
  children,
  open: openProp,
  setOpen: setOpenProp,
}: {
  children: React.ReactNode;
  open?: boolean;
  setOpen?: React.Dispatch<React.SetStateAction<boolean>>;
}) => {
  const [openState, setOpenState] = useState(false);

  const open = openProp !== undefined ? openProp : openState;
  const setOpen = setOpenProp !== undefined ? setOpenProp : setOpenState;

  return (
    <SidebarContext.Provider value={{ open, setOpen }}>
      {children}
    </SidebarContext.Provider>
  );
};

export const Sidebar = ({
  children,
  open,
  setOpen,
}: {
  children: React.ReactNode;
  open?: boolean;
  setOpen?: React.Dispatch<React.SetStateAction<boolean>>;
}) => {
  return (
    <SidebarProvider open={open} setOpen={setOpen}>
      {children}
    </SidebarProvider>
  );
};

export const SidebarBody = (props: React.ComponentProps<typeof motion.div>) => {
  return (
    <>
      <DesktopSidebar {...props} />
      <MobileSidebar {...(props as React.ComponentProps<"div">)} />
    </>
  );
};

export const DesktopSidebar = ({
  className,
  children,
  ...props
}: React.ComponentProps<typeof motion.div>) => {
  const { open, setOpen } = useSidebar();
  return (
    <>
      <motion.div
        className={cn(
          "h-full hidden md:flex md:flex-col bg-neutral-100 dark:bg-neutral-800 relative",
          className
        )}
        animate={{
          width: open ? "300px" : "80px",
        }}
        transition={{
          duration: 0.3,
          ease: "easeInOut"
        }}
        onMouseEnter={() => setOpen(true)}
        onMouseLeave={() => setOpen(false)}
        {...props}
      >
        {children}
      </motion.div>
    </>
  );
};

export const MobileSidebar = ({
  className,
  children,
  ...props
}: React.ComponentProps<"div">) => {
  const { open, setOpen } = useSidebar();
  return (
    <>
      <div
        className={cn(
          "h-10 px-4 py-4 flex flex-row md:hidden items-center justify-between bg-neutral-100 dark:bg-neutral-800 w-full"
        )}
        {...props}
      >
        <div className="flex justify-end z-20 w-full">
          <IconMenu2
            className="text-neutral-800 dark:text-neutral-200"
            onClick={() => setOpen(!open)}
          />
        </div>
        <AnimatePresence>
          {open && (
            <motion.div
              initial={{ x: "-100%", opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              exit={{ x: "-100%", opacity: 0 }}
              transition={{
                duration: 0.3,
                ease: "easeInOut",
              }}
              className={cn(
                "fixed h-full w-full inset-0 bg-white dark:bg-neutral-900 p-10 z-[100] flex flex-col justify-between",
                className
              )}
            >
              <div
                className="absolute right-10 top-10 z-50 text-neutral-800 dark:text-neutral-200"
                onClick={() => setOpen(!open)}
              >
                <IconX />
              </div>
              {children}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </>
  );
};

export const SidebarLink = ({
  link,
  className,
  ...props
}: {
  link: Links;
  className?: string;
}) => {
  const { open } = useSidebar();
  
  return (
    <a
      href={link.href}
      className={cn(
        "flex items-center group/sidebar relative h-12",
        className
      )}
      {...props}
    >
      {/* Icon container - fixed position regardless of sidebar state */}
      <div className="absolute left-0 w-20 flex justify-center items-center h-full">
        <div className="scale-[1.2]">{link.icon}</div>
      </div>
      
      {/* Text container - appears on hover */}
      <AnimatePresence>
        {open && (
          <motion.span
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="absolute left-20 text-neutral-700 dark:text-neutral-200 text-base font-medium whitespace-nowrap overflow-hidden"
          >
            {link.label}
          </motion.span>
        )}
      </AnimatePresence>
    </a>
  );
};

export const Logo = () => {
  const { open } = useSidebar();
  
  return (
    <div className="relative h-16 flex items-center">
      {/* Logo is always centered in the collapsed sidebar width */}
      <div className="absolute left-0 w-20 flex justify-center">
        <div className="flex-shrink-0">
          <Image src="/reallogo.png" alt="Bluebox" width={40} height={40} />
        </div>
      </div>
      
      {/* Text appears on hover */}
      <AnimatePresence>
        {open && (
          <motion.span
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="absolute left-20 font-medium whitespace-nowrap text-black dark:text-white text-lg overflow-hidden"
          >
            Explore the Bluebox!
          </motion.span>
        )}
      </AnimatePresence>
    </div>
  );
};

export const SidebarMenu = () => {
  // Simplified set of links
  const menuLinks = [
    {
      label: "New chat",
      href: "#",
      icon: <IconBrandTabler className="h-5 w-5 shrink-0 text-neutral-700 dark:text-neutral-200" />,
    },
    {
      label: "Past chats",
      href: "#",
      icon: <IconUserBolt className="h-5 w-5 shrink-0 text-neutral-700 dark:text-neutral-200" />,
    },
  ];
  
  return (
    <SidebarBody className="justify-between flex-col">
      <div className="flex flex-1 flex-col">
        <Logo />
        <div className="mt-10 flex flex-col">
          {menuLinks.map((link, idx) => (
            <SidebarLink key={idx} link={link} />
          ))}
        </div>
      </div>
      <div className="mt-auto">
        <SidebarLink
          link={{
            label: "Your Profile",
            href: "#",
            icon: (
              <div className="h-8 w-8 shrink-0 rounded-full bg-neutral-300 dark:bg-neutral-600 grid place-items-center">
                <span className="text-xs text-neutral-700 dark:text-neutral-200">N</span>
              </div>
            ),
          }}
        />
      </div>
    </SidebarBody>
  );
};
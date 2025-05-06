// components/SidebarNav.tsx
'use client';
import { useState, useRef, useEffect } from "react";
import Link from "next/link";

export default function SidebarNav() {
  const [open, setOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  // Close the menu if you click outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setOpen(false);
      }
    }
    if (open) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [open]);

  return (
    <>
      <div className="fixed top-6 right-6 z-50">
        <button
          className="menu-btn-background flex items-center gap-3 px-6 py-2 group"
          onClick={() => setOpen((v) => !v)}
          aria-label="Open menu"
          style={{ minWidth: 120, borderRadius: 9999, height: 48 }}
        >
          <span className="text-[#222] font-medium text-base select-none" style={{ letterSpacing: '0.05em' }}>
            MENU
          </span>
          <span className="menu__icon">
            <span></span>
            <span></span>
            <span></span>
          </span>
        </button>
        {open && (
          <div
            ref={menuRef}
            className="absolute right-0 mt-3 w-80 bg-white rounded-2xl shadow-2xl border border-gray-400 py-6 z-50 animate-fade-in"
            style={{ minHeight: 260 }}
          >
            <ul className="flex flex-col gap-4 px-8">
              <li>
                <Link href="#use-cases" onClick={() => setOpen(false)} className="block py-3 px-4 rounded-lg hover:bg-blue-100 text-lg font-semibold text-gray-900 transition">
                  Use cases
                </Link>
              </li>
              <li>
                <Link href="#community" onClick={() => setOpen(false)} className="block py-3 px-4 rounded-lg hover:bg-blue-100 text-lg font-semibold text-gray-900 transition">
                  Community
                </Link>
              </li>
              <li>
                <Link href="#benchmarks" onClick={() => setOpen(false)} className="block py-3 px-4 rounded-lg hover:bg-blue-100 text-lg font-semibold text-gray-900 transition">
                  Benchmarks
                </Link>
              </li>
              <li>
                <Link href="#pricing" onClick={() => setOpen(false)} className="block py-3 px-4 rounded-lg hover:bg-blue-100 text-lg font-semibold text-gray-900 transition">
                  Pricing
                </Link>
              </li>
            </ul>
          </div>
        )}
      </div>
    </>
  );
}
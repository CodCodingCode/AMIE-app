"use client";
import React from "react";
import Link from "next/link";

export const Navigation = () => {
  return (
    <div className="fixed top-10 inset-x-0 max-w-2xl mx-auto z-50">
      <nav className="navbar">
        <Link href='#Home' className="navbar-item">Home</Link>
        <Link href="#Video" className="navbar-item">Video</Link>
        <Link href="#about" className="navbar-item">About</Link>
        <Link href="#benchmarks" className="navbar-item">Benchmarks</Link>
        <Link href="#footer" className="navbar-item">Contact</Link>
      </nav>
    </div>
  );
};

export default Navigation;
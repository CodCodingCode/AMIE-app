'use client'

import Hero from './components/hero'
import Footer from './components/footer'
import Navigation from './components/navigation'
import Gif from './components/gif'

export default function Home() {
  return (
    <div className="flex flex-col bg-gradient-to-b from-neutral-900 to-neutral-950">
      <Navigation />
      <Hero />
      <Gif />
      <Footer />
    </div>
  );
}
'use client'

import Hero from './components/hero'
import Features from './components/features'
import Benefits from './components/benefits'
import Testimonials from './components/testimonials'
import CallToAction from './components/cta'
import Footer from './components/footer'
import Navigation from './components/navigation'

export default function Home() {
  return (
    <div className="flex flex-col bg-gradient-to-b from-neutral-900 to-neutral-950">
      <Navigation />
      <Hero />
      <Features />
      <Benefits />
      <Testimonials />
      <CallToAction />
      <Footer />
    </div>
  );
}
'use client'

import About from './components/about'
import PortalScene from './portalcomps/portalcomplete'
import Benchmarks from './components/benchmarks'
import Footer from './components/footer'
import Navigation from './components/navigation'
import Videopage from './components/videopage'

export default function Home() {
  return (
    <div className="flex flex-col">
      <Navigation />
      <section id="Home">
        <PortalScene />
      </section>
      <section id="Video">
        <Videopage />
      </section>
      <section id="About">
        <About />
      </section>
      <section id="Benchmarks">
        <Benchmarks />
      </section>
      <Footer />
    </div>
  );
}
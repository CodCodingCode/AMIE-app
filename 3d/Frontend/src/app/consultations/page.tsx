'use client';

import React from 'react';
import { motion } from 'framer-motion';
import BackButton from '../components/backbutton';

export default function ConsultationsPage () {
   return (
       <motion.div className="min-h-screen bg-neutral-900 text-white">
           {/* Header matching settings page */}
           <header className="bg-neutral-900 border-b border-trueBlue p-4 flex items-center">
               <BackButton />
               <h1 className="text-2xl font-serif text-dukeBlue font-semibold mx-auto pr-10">
                   Consultations
               </h1>
           </header>

           {/* Main content placeholder */}
           <main className="max-w-2xl mx-auto p-6">
               {/* Content goes here */}
           </main>
       </motion.div>
   );
}
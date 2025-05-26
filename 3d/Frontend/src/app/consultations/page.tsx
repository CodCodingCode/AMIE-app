'use client';


import React from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '../chat/Auth';
import { IconLogout, IconArrowLeft } from '@tabler/icons-react';
import { motion } from 'framer-motion';


export default function ConsultationsPage () {
   const router = useRouter();

   const handleBack = () => {
       router.back();
   }


   return (
       <motion.div>
           <div className="flex items-center justify-between">
           <button 
            onClick={handleBack}
            className="flex items-center text-mountbattenPink hover:text-dukeBlue transition-colors"
            >
            <IconArrowLeft size={20} className="mr-2" />
            <span>Back</span>
            </button>
               <h1 className="text-2xl font-serif text-dukeBlue font-semibold mx-auto pr-10">
          Consultations
        </h1>
        <button 
          onClick={handleBack}
          className="flex items-center text-mountbattenPink hover:text-dukeBlue transition-colors"
        >
          <IconArrowLeft size={20} className="mr-2" />
          <span>Back</span>
        </button>
           </div>
       </motion.div>
   )
  
}


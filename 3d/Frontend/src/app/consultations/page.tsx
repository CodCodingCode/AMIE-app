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
               <button onClick={handleBack}>
                   <IconArrowLeft />
               </button>
               <h1>Consultations</h1>
           </div>
       </motion.div>
   )
  
}


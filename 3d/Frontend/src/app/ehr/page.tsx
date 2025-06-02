'use client';
import { FileUpload } from "./file";
import React from "react";
import BackButton from "../components/backbutton";

export default function EhrPage() {
   const handleFileUpload = (files: File[]) => {
       console.log(files);
   };

   return (
       <div className="min-h-screen bg-neutral-900 text-white relative">
           {/* Back button at top left */}
           <div className="absolute top-4 left-4 z-10">
               <BackButton 
                   to="/chat"
                   label="Back to Dashboard"
                   variant="minimal"
                   size="md"
               />
           </div>

           {/* Header */}
           <header className="bg-neutral-900 border-b border-trueBlue p-6 pt-16">
               <div className="max-w-4xl mx-auto text-center">
                   <h1 className="text-2xl font-serif text-dukeBlue font-semibold">
                       EHR File Upload
                   </h1>
               </div>
           </header>

           {/* Content */}
           <main className="max-w-2xl mx-auto p-6 flex flex-col items-center justify-center">
               <FileUpload onChange={handleFileUpload} />
           </main>
       </div>
   );
}
'use client';
import { FileUpload } from "./file";
import React from "react";
import BackButton from "../components/backbutton";

export default function EhrPage() {
   const handleFileUpload = (files: File[]) => {
       console.log(files);
   };

   return (
       <div className="min-h-screen bg-neutral-900 text-white">
           {/* Header matching settings page */}
           <header className="bg-neutral-900 border-b border-trueBlue p-4 flex items-center">
               <BackButton />
               <h1 className="text-2xl font-serif text-dukeBlue font-semibold mx-auto pr-10">
                   EHR File Upload
               </h1>
           </header>

           {/* Content */}
           <main className="max-w-2xl mx-auto p-6 flex flex-col items-center justify-center">
               <FileUpload onChange={handleFileUpload} />
           </main>
       </div>
   );
}
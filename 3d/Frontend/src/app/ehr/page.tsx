'use client';
import { useRouter } from "next/navigation";
import { FileUpload } from "./file";
import React from "react";
import { IconArrowLeft } from "@tabler/icons-react";

export default function EhrPage() {
   const router = useRouter();

    const handleBack = () => {
        router.back();
    };

   const handleFileUpload = (files: File[]) => {
       console.log(files);
   };


   return (
       <div className="flex flex-col items-center justify-center h-screen bg-neutral-900 px-4">
        <header>
            <button 
                onClick={handleBack}
                className="flex items-center text-mountbattenPink hover:text-dukeBlue transition-colors"
                >
                <IconArrowLeft size={20} className="mr-2" />
                <span>Back</span>
            </button>
        </header>
           <h1 className="text-2xl font-semibold mb-6">EHR File Upload</h1>
           <FileUpload onChange={handleFileUpload} />
       </div>
   );
}
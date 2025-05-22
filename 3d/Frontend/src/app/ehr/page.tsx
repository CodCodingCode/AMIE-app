'use client';
import { useRouter } from "next/navigation";
import { FileUpload } from "./file";
import React from "react";


export default function EhrPage() {
   const router = useRouter();


   const handleFileUpload = (files: File[]) => {
       console.log(files);
   };


   return (
       <div className="flex flex-col items-center justify-center h-screen bg-white px-4">
           <h1 className="text-2xl font-semibold mb-6">EHR File Upload</h1>
           <FileUpload onChange={handleFileUpload} />
       </div>
   );
}




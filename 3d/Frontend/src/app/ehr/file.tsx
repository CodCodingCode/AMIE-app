import { cn } from "../lib/utils";
import React, { useRef, useState } from "react";
import { motion } from "motion/react";
import { IconUpload } from "@tabler/icons-react";
import { useDropzone } from "react-dropzone";


export const FileUpload = ({
 onChange,
}: {
 onChange?: (files: File[]) => void;
}) => {
 const [files, setFiles] = useState<File[]>([]);
 const fileInputRef = useRef<HTMLInputElement>(null);


 const handleFileChange = (newFiles: File[]) => {
   setFiles((prevFiles) => [...prevFiles, ...newFiles]);
   onChange && onChange(newFiles);
 };


 const handleClick = () => {
   fileInputRef.current?.click();
 };


 const { getRootProps, isDragActive } = useDropzone({
   multiple: false,
   noClick: true,
   onDrop: handleFileChange,
   onDropRejected: (error) => {
     console.log(error);
   },
 });


 return (
   <div className="w-full max-w-2xl" {...getRootProps()}>
     <motion.div
       onClick={handleClick}
       whileHover="animate"
       className="p-8 group/file block rounded-xl cursor-pointer w-full relative bg-white border border-gray-200 shadow-md transition hover:shadow-lg"
     >
       <input
         ref={fileInputRef}
         id="file-upload-handle"
         type="file"
         onChange={(e) => handleFileChange(Array.from(e.target.files || []))}
         className="hidden"
       />


       <div className="flex flex-col items-center justify-center text-center">
         <p className="font-semibold text-gray-700 text-base">
           Upload file
         </p>
         <p className="text-sm text-gray-500 mt-2">
           Drag or drop your files here or click to upload
         </p>


         <div className="relative w-full mt-8 max-w-xl mx-auto">
           {files.length > 0 &&
             files.map((file, idx) => (
               <motion.div
                 key={"file" + idx}
                 layoutId={idx === 0 ? "file-upload" : "file-upload-" + idx}
                 className={cn(
                   "bg-white flex flex-col items-start justify-start md:h-24 p-4 mt-4 w-full mx-auto rounded-md border border-gray-200 shadow-sm"
                 )}
               >
                 <div className="flex justify-between w-full items-center gap-4">
                   <motion.p
                     initial={{ opacity: 0 }}
                     animate={{ opacity: 1 }}
                     layout
                     className="text-sm text-gray-800 truncate max-w-xs"
                   >
                     {file.name}
                   </motion.p>
                   <motion.p
                     initial={{ opacity: 0 }}
                     animate={{ opacity: 1 }}
                     layout
                     className="rounded-lg px-2 py-1 w-fit text-sm text-gray-600 bg-gray-100"
                   >
                     {(file.size / (1024 * 1024)).toFixed(2)} MB
                   </motion.p>
                 </div>


                 <div className="flex text-sm md:flex-row flex-col items-start md:items-center w-full mt-2 justify-between text-gray-500">
                   <motion.p
                     initial={{ opacity: 0 }}
                     animate={{ opacity: 1 }}
                     layout
                     className="px-1 py-0.5 rounded bg-gray-100"
                   >
                     {file.type}
                   </motion.p>
                   <motion.p
                     initial={{ opacity: 0 }}
                     animate={{ opacity: 1 }}
                     layout
                   >
                     modified {new Date(file.lastModified).toLocaleDateString()}
                   </motion.p>
                 </div>
               </motion.div>
             ))}


           {!files.length && (
             <motion.div
               layoutId="file-upload"
               variants={{
                 initial: { opacity: 0 },
                 animate: { opacity: 1 },
               }}
               transition={{
                 type: "spring",
                 stiffness: 300,
                 damping: 20,
               }}
               className="flex flex-col items-center justify-center h-32 mt-4 w-full max-w-[8rem] mx-auto rounded-md border border-dashed border-gray-300"
             >
               {isDragActive ? (
                 <p className="text-gray-600 text-sm flex flex-col items-center">
                   Drop it
                   <IconUpload className="h-4 w-4 mt-1 text-gray-500" />
                 </p>
               ) : (
                 <IconUpload className="h-5 w-5 text-gray-500" />
               )}
             </motion.div>
           )}
         </div>
       </div>
     </motion.div>
   </div>
 );
};
'use client';

import { cn, fadeInUp, staggerContainer, defaultTransition } from "@/app/lib/utils";
import React, { useRef, useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { IconUpload, IconFile, IconX, IconLoader2, IconAlertCircle, IconCheckCircle } from "@tabler/icons-react";
import { useDropzone, FileRejection } from "react-dropzone";
import { useEhr } from "@/app/contexts/EhrContext";
import { useRouter } from "next/navigation";

const FileItem: React.FC<{ file: File; onRemove: () => void }> = ({ file, onRemove }) => (
  <motion.div
    layout
    initial={{ opacity: 0, y: -10 }}
    animate={{ opacity: 1, y: 0 }}
    exit={{ opacity: 0, x: -20 }}
    transition={{ duration: 0.3 }}
    className="relative bg-neutral-800 flex items-center p-3 my-2 w-full rounded-lg shadow border border-neutral-700"
  >
    <IconFile className="w-6 h-6 text-blue-400 mr-3 flex-shrink-0" />
    <div className="flex-1 min-w-0">
      <p className="text-sm text-neutral-200 truncate font-medium">{file.name}</p>
      <p className="text-xs text-neutral-400">
        {(file.size / (1024 * 1024)).toFixed(2)} MB - {file.type}
      </p>
    </div>
    <button 
      onClick={onRemove}
      className="ml-2 p-1 text-neutral-500 hover:text-red-400 hover:bg-red-500/10 rounded-full transition-colors"
      title="Remove file"
    >
      <IconX size={18} />
    </button>
  </motion.div>
);

const GridPattern = React.memo(() => {
  const columns = 40;
  const rows = 10;
  return (
    <div className="absolute inset-0 [mask-image:radial-gradient(ellipse_at_center,white_20%,transparent_70%)] pointer-events-none">
      <div className="absolute inset-0 flex flex-wrap justify-center items-center gap-px opacity-30">
        {Array.from({ length: rows * columns }).map((_, index) => (
          <div
            key={index}
            className={`w-10 h-10 rounded-sm ${
              index % 2 === 0 ? "bg-neutral-700/50" : "bg-neutral-800/50"
            }`}
          />
        ))}
      </div>
    </div>
  );
});
GridPattern.displayName = 'GridPattern';

export const FileUpload: React.FC<{ onChange?: (files: File[]) => void }> = ({ onChange }) => {
  const [files, setFiles] = useState<File[]>([]);
  const [processing, setProcessing] = useState<boolean>(false);
  const [processedData, setProcessedData] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  
  const { setEhrSummary, consumeEhrSummary } = useEhr(); // consumeEhrSummary might be useful elsewhere
  const router = useRouter();

  const handleFileUpload = useCallback(async (fileToProcess: File) => {
    setProcessing(true);
    setProcessedData(null);
    setError(null);
    setEhrSummary(null); // Clear previous summary

    const formData = new FormData();
    formData.append("file", fileToProcess);

    try {
      const response = await fetch("http://127.0.0.1:5001/api/process-file", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        let errorMsg = `HTTP error! status: ${response.status}`;
        try {
          const errData = await response.json();
          errorMsg = errData.error || errData.message || errorMsg;
        } catch {}
        throw new Error(errorMsg);
      }

      const result = await response.json();
      if (!result.response) throw new Error('No response data from server.');
      
      setProcessedData(result.response);
      setEhrSummary(result.response);
      setFiles([]); // Clear file list after successful processing
    } catch (e: any) {
      console.error("Upload failed:", e);
      setError(e.message || "Failed to process file. Please try again.");
    } finally {
      setProcessing(false);
    }
  }, [setEhrSummary]);

  const onDrop = useCallback((acceptedFiles: File[], fileRejections: FileRejection[]) => {
    setError(null); // Clear previous errors
    if (fileRejections.length > 0) {
      setError(`File rejected: ${fileRejections[0].errors[0].message}. Please upload a valid file.`);
      return;
    }
    if (acceptedFiles.length > 0) {
      setFiles(acceptedFiles); // Replace, as we process one by one
      onChange?.(acceptedFiles);
      handleFileUpload(acceptedFiles[0]); // Process the first (and only accepted) file
    }
  }, [onChange, handleFileUpload]);

  const { getRootProps, getInputProps, isDragActive, open } = useDropzone({
    onDrop,
    multiple: false, // Allow only single file upload as per current logic
    accept: { // Example: common document types, adjust as needed
      'application/pdf': ['.pdf'],
      'text/plain': ['.txt'],
      'application/msword': ['.doc'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx']
    }
  });

  const removeFile = (indexToRemove: number) => {
    setFiles(prevFiles => prevFiles.filter((_, index) => index !== indexToRemove));
    // If current processing file is removed, consider cancelling the upload if possible
    // For now, it will continue processing, but UI will reflect removal.
  };

  const renderStatus = () => {
    if (processing) {
      return (
        <motion.div {...fadeInUp} className="flex items-center justify-center text-neutral-400 p-4">
          <IconLoader2 className="animate-spin w-5 h-5 mr-2" />
          Processing your file, please wait...
        </motion.div>
      );
    }
    if (error) {
      return (
        <motion.div {...fadeInUp} className="text-red-400 bg-red-900/30 p-4 rounded-md border border-red-700/50 flex items-start">
          <IconAlertCircle className="w-5 h-5 mr-2 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-semibold">Upload Failed</p>
            <p className="text-sm">{error}</p>
          </div>
        </motion.div>
      );
    }
    if (processedData) {
      return (
        <motion.div {...fadeInUp} className="p-4 bg-green-900/30 rounded-md border border-green-700/50">
          <div className="flex items-start mb-2">
            <IconCheckCircle className="w-5 h-5 mr-2 text-green-400 flex-shrink-0 mt-0.5" />
            <h3 className="font-semibold text-green-300">File Processed Successfully</h3>
          </div>
          <p className="text-sm text-neutral-300 mb-3">Summary has been generated and is ready for your chat.</p>
          <pre className="whitespace-pre-wrap text-xs text-neutral-400 bg-neutral-800 p-3 rounded-md max-h-40 overflow-y-auto no-scrollbar mb-4">
            {processedData}
          </pre>
          <button 
            onClick={() => router.push('/chat')} 
            className="w-full px-4 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium text-sm"
          >
            Go to Chat
          </button>
        </motion.div>
      );
    }
    return null;
  };

  return (
    <div className="w-full max-w-lg mx-auto mt-8 p-6 bg-neutral-850 rounded-xl shadow-2xl border border-neutral-700/80">
      <GridPattern />
      <div 
        {...getRootProps()} 
        className={cn(
          "relative flex flex-col items-center justify-center p-8 border-2 border-dashed rounded-xl cursor-pointer transition-all duration-200 ease-in-out",
          isDragActive ? "border-blue-500 bg-blue-500/10" : "border-neutral-700 hover:border-neutral-600",
          (files.length > 0 || processing || processedData || error) && "border-transparent hover:border-transparent cursor-default"
        )}
      >
        <input {...getInputProps()} />
        
        {!files.length && !processing && !processedData && !error && (
          <>
            <IconUpload className={`w-12 h-12 mb-4 ${isDragActive ? 'text-blue-400' : 'text-neutral-500'} transition-colors`} />
            <p className={`text-lg font-semibold ${isDragActive ? 'text-blue-300' : 'text-neutral-300'}`}>Drag & Drop File Here</p>
            <p className="text-sm text-neutral-500 mt-1">or</p>
            <button 
              type="button" 
              onClick={open} 
              className="mt-3 px-5 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition-colors"
            >
              Browse Files
            </button>
            <p className="text-xs text-neutral-600 mt-4">Supports PDF, DOCX, TXT (Max 5MB)</p>
          </>
        )}

        {(files.length > 0 && !processedData && !error) && (
          <div className="w-full">
            <h3 className="text-sm font-medium text-neutral-400 mb-2 text-center">Selected file:</h3>
            {files.map((file, idx) => (
              <FileItem key={idx} file={file} onRemove={() => removeFile(idx)} />
            ))}
          </div>
        )}

        <div className="w-full mt-4 min-h-[60px]"> {/* Placeholder for status messages */}
          {renderStatus()}
        </div>
      </div>
    </div>
  );
};

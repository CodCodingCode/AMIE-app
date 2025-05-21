import { cn } from "../lib/utils";
import React, { useRef, useState } from "react";
import { motion } from "motion/react";
import { IconUpload } from "@tabler/icons-react";
import { useDropzone } from "react-dropzone";
import { useEhr } from "../contexts/EhrContext";
import { useRouter } from "next/navigation";

// Animation Variants
const mainVariant = {
  initial: { x: 0, y: 0 },
  animate: { x: 20, y: -20, opacity: 0.9 },
};

const secondaryVariant = {
  initial: { opacity: 0 },
  animate: { opacity: 1 },
};

export const FileUpload = ({
  onChange,
}: {
  onChange?: (files: File[]) => void;
}) => {
  const [files, setFiles] = useState<File[]>([]);
  const [processing, setProcessing] = useState<boolean>(false);
  const [processedData, setProcessedData] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const uploadContainerRef = useRef<HTMLDivElement>(null);

  const { setEhrSummary } = useEhr();
  const router = useRouter();

  const handleFileChange = (newFiles: File[]) => {
    setFiles((prevFiles) => [...prevFiles, ...newFiles]);
    onChange && onChange(newFiles);

    if (newFiles.length > 0) {
      const fileToProcess = newFiles[0];
      handleFileUpload(fileToProcess);
    }

    setTimeout(() => {
      uploadContainerRef.current?.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
    }, 100);
  };

  const handleClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileUpload = async (file: File) => {
    setProcessing(true);
    setProcessedData(null);
    setError(null);
    setEhrSummary(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch("http://127.0.0.1:5001/api/process-file", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.error || `HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      setProcessedData(result.response);
      setEhrSummary(result.response);
    } catch (e: any) {
      console.error("Upload failed", e);
      setError(e.message || "Failed to process file.");
    } finally {
      setProcessing(false);
    }
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
    <div className="w-full max-w-2xl" {...getRootProps()} ref={uploadContainerRef}>
      <motion.div
        whileHover="animate"
        className="p-10 group/file block rounded-xl w-full relative overflow-hidden border border-gray-200 bg-white dark:bg-neutral-900 shadow-md transition hover:shadow-lg"
      >
        <input
          ref={fileInputRef}
          id="file-upload-handle"
          type="file"
          onChange={(e) => handleFileChange(Array.from(e.target.files || []))}
          className="hidden"
        />

        {/* Grid background */}
        <div className="absolute inset-0 [mask-image:radial-gradient(ellipse_at_center,white,transparent)] pointer-events-none">
          <GridPattern />
        </div>

        <div className="flex flex-col items-center justify-center text-center relative z-10">
          <p className="font-bold text-neutral-700 dark:text-neutral-300 text-base">Upload file</p>
          <p className="text-base text-neutral-400 mt-2">Drag or drop your files here or click to upload</p>

          <div className="relative w-full mt-10 max-w-xl mx-auto">
            {files.length > 0 &&
              files.map((file, idx) => (
                <motion.div
                  key={"file" + idx}
                  layoutId={idx === 0 ? "file-upload" : "file-upload-" + idx}
                  className={cn(
                    "relative z-40 bg-white dark:bg-neutral-900 flex flex-col items-start justify-start md:h-24 p-4 mt-4 w-full mx-auto rounded-md shadow-sm border border-gray-200 dark:border-neutral-700"
                  )}
                >
                  <div className="flex justify-between w-full items-center gap-4">
                    <motion.p
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      layout
                      className="text-base text-neutral-700 dark:text-neutral-300 truncate max-w-xs"
                    >
                      {file.name}
                    </motion.p>
                    <motion.p
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      layout
                      className="rounded-lg px-2 py-1 w-fit shrink-0 text-sm text-neutral-600 dark:bg-neutral-800 dark:text-white shadow-input"
                    >
                      {(file.size / (1024 * 1024)).toFixed(2)} MB
                    </motion.p>
                  </div>

                  <div className="flex text-sm md:flex-row flex-col items-start md:items-center w-full mt-2 justify-between text-neutral-600 dark:text-neutral-400">
                    <motion.p
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      layout
                      className="px-1 py-0.5 rounded-md bg-gray-100 dark:bg-neutral-800"
                    >
                      {file.type}
                    </motion.p>
                    <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} layout>
                      modified {new Date(file.lastModified).toLocaleDateString()}
                    </motion.p>
                  </div>
                </motion.div>
              ))}

            {processing && (
              <motion.div
                layoutId="processing-indicator"
                className="text-center p-4 mt-4 w-full mx-auto text-neutral-600 dark:text-neutral-400"
              >
                <p>Processing your file, please wait...</p>
              </motion.div>
            )}

            {error && (
              <motion.div
                layoutId="error-message"
                className="text-center p-4 mt-4 w-full mx-auto text-red-500 bg-red-100 dark:bg-red-900 dark:text-red-300 rounded-md border border-red-500"
              >
                <p>Error: {error}</p>
              </motion.div>
            )}

            {processedData && (
              <motion.div
                layoutId="processed-data"
                className="p-4 mt-4 w-full mx-auto rounded-md shadow-sm border border-gray-200 dark:border-neutral-700 bg-white dark:bg-neutral-800"
              >
                <h3 className="font-semibold text-neutral-700 dark:text-neutral-300 mb-2">Processed Information:</h3>
                <pre className="whitespace-pre-wrap text-sm text-neutral-600 dark:text-neutral-400">{processedData}</pre>
                <button 
                  onClick={() => router.push('/chat')} 
                  className="mt-4 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
                >
                  Go to Chat
                </button>
              </motion.div>
            )}

            {!files.length && !processing && (
              <motion.div
                layoutId="file-upload"
                onClick={handleClick}
                variants={mainVariant}
                transition={{ type: "spring", stiffness: 300, damping: 20 }}
                className={cn(
                  "relative z-40 bg-white dark:bg-neutral-900 flex items-center justify-center h-32 mt-4 w-full max-w-[8rem] mx-auto rounded-md",
                  "shadow-[0px_10px_50px_rgba(0,0,0,0.1)] cursor-pointer"
                )}
              >
                {isDragActive ? (
                  <motion.p
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="text-neutral-600 flex flex-col items-center"
                  >
                    Drop it
                    <IconUpload className="h-4 w-4 mt-1 text-neutral-600 dark:text-neutral-400" />
                  </motion.p>
                ) : (
                  <IconUpload className="h-4 w-4 text-neutral-600 dark:text-neutral-300" />
                )}
              </motion.div>
            )}

            {!files.length && (
              <motion.div
                variants={secondaryVariant}
                className="absolute opacity-0 border border-dashed border-sky-400 inset-0 z-30 bg-transparent flex items-center justify-center h-32 mt-4 w-full max-w-[8rem] mx-auto rounded-md"
              ></motion.div>
            )}
          </div>
        </div>
      </motion.div>
    </div>
  );
};

export function GridPattern() {
  const columns = 41;
  const rows = 11;
  return (
    <div className="flex bg-gray-100 dark:bg-neutral-900 shrink-0 flex-wrap justify-center items-center gap-x-px gap-y-px scale-105">
      {Array.from({ length: rows }).map((_, row) =>
        Array.from({ length: columns }).map((_, col) => {
          const index = row * columns + col;
          return (
            <div
              key={`${col}-${row}`}
              className={`w-10 h-10 flex shrink-0 rounded-[2px] ${
                index % 2 === 0
                  ? "bg-gray-50 dark:bg-neutral-950"
                  : "bg-gray-50 dark:bg-neutral-950 shadow-[0px_0px_1px_3px_rgba(255,255,255,1)_inset] dark:shadow-[0px_0px_1px_3px_rgba(0,0,0,1)_inset]"
              }`}
            />
          );
        })
      )}
    </div>
  );
}

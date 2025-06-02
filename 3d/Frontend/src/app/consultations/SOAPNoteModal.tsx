'use client';

import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { IconX, IconDownload, IconCopy, IconFileText, IconCheck } from '@tabler/icons-react';
import { SOAPNote } from '../chat/chatService'; // Assuming SOAPNote type is exported

interface SOAPNoteModalProps {
  isOpen: boolean;
  onClose: () => void;
  soapNote: SOAPNote | null;
  onSave?: (note: SOAPNote) => void; // Optional: if editing/saving from modal is needed
}

const SOAPNoteModal: React.FC<SOAPNoteModalProps> = ({ isOpen, onClose, soapNote }) => {
  const [copied, setCopied] = React.useState(false);

  if (!soapNote) return null;

  const fullSoapText = `Subjective:\n${soapNote.subjective}\n\nObjective:\n${soapNote.objective}\n\nAssessment:\n${soapNote.assessment}\n\nPlan:\n${soapNote.plan.join('\n- ')}`;

  const handleCopy = () => {
    navigator.clipboard.writeText(fullSoapText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    const blob = new Blob([fullSoapText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `SOAP_Note_${soapNote.chatId}_${new Date().toISOString().split('T')[0]}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4"
          onClick={onClose}
        >
          <motion.div
            initial={{ scale: 0.9, opacity: 0, y: 20 }}
            animate={{ scale: 1, opacity: 1, y: 0 }}
            exit={{ scale: 0.9, opacity: 0, y: 20 }}
            transition={{ type: 'spring', stiffness: 300, damping: 30 }}
            onClick={(e) => e.stopPropagation()}
            className="bg-neutral-800 rounded-xl shadow-2xl w-full max-w-2xl border border-neutral-700 flex flex-col max-h-[90vh]"
          >
            <header className="p-4 sm:p-5 border-b border-neutral-700 flex items-center justify-between">
              <div className="flex items-center">
                <IconFileText className="w-6 h-6 text-blue-400 mr-3" />
                <h2 className="text-lg font-semibold text-white">SOAP Note</h2>
              </div>
              <button 
                onClick={onClose} 
                className="p-1.5 rounded-md text-neutral-400 hover:bg-neutral-700 hover:text-neutral-100 transition-colors"
                aria-label="Close modal"
              >
                <IconX size={20} />
              </button>
            </header>

            <main className="p-4 sm:p-6 flex-grow overflow-y-auto no-scrollbar">
              <div className="space-y-4">
                <div>
                  <h3 className="text-sm font-semibold text-blue-300 mb-1">Subjective</h3>
                  <p className="text-sm text-neutral-300 whitespace-pre-wrap bg-neutral-700/50 p-3 rounded-md">{soapNote.subjective || 'N/A'}</p>
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-blue-300 mb-1">Objective</h3>
                  <p className="text-sm text-neutral-300 whitespace-pre-wrap bg-neutral-700/50 p-3 rounded-md">{soapNote.objective || 'N/A'}</p>
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-blue-300 mb-1">Assessment</h3>
                  <p className="text-sm text-neutral-300 whitespace-pre-wrap bg-neutral-700/50 p-3 rounded-md">{soapNote.assessment || 'N/A'}</p>
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-blue-300 mb-1">Plan</h3>
                  <ul className="list-disc list-inside text-sm text-neutral-300 space-y-1 bg-neutral-700/50 p-3 rounded-md">
                    {soapNote.plan && soapNote.plan.length > 0 ? soapNote.plan.map((item, index) => (
                      <li key={index}>{item}</li>
                    )) : <li>N/A</li>}
                  </ul>
                </div>
              </div>
              <p className="text-xs text-neutral-500 mt-4 text-right">
                Generated: {new Date(soapNote.generatedAt).toLocaleString()}
              </p>
            </main>

            <footer className="p-4 sm:p-5 border-t border-neutral-700 flex flex-col sm:flex-row items-center justify-end space-y-3 sm:space-y-0 sm:space-x-3">
              <button
                onClick={handleCopy}
                className="w-full sm:w-auto px-4 py-2.5 bg-neutral-700 hover:bg-neutral-600 text-neutral-200 rounded-lg transition-colors flex items-center justify-center text-sm font-medium"
              >
                {copied ? <IconCheck className="w-4 h-4 mr-2 text-green-400" /> : <IconCopy className="w-4 h-4 mr-2" />}
                {copied ? 'Copied!' : 'Copy Text'}
              </button>
              <button
                onClick={handleDownload}
                className="w-full sm:w-auto px-4 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors flex items-center justify-center text-sm font-medium"
              >
                <IconDownload className="w-4 h-4 mr-2" />
                Download .txt
              </button>
            </footer>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default SOAPNoteModal; 
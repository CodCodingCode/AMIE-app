'use client';

import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { IconX, IconSend, IconDownload, IconCopy, IconCheck, IconUsers } from '@tabler/icons-react';
import { Referral } from '../chat/chatService'; // Assuming Referral type is exported

interface ReferralModalProps {
  isOpen: boolean;
  onClose: () => void;
  referral: Referral | null;
  // onSend?: (referral: Referral) => void; // If sending/updating from modal is needed
}

const ReferralModal: React.FC<ReferralModalProps> = ({ isOpen, onClose, referral }) => {
  const [copied, setCopied] = React.useState(false);

  if (!referral) return null;

  const fullReferralText = 
`Referral To: ${referral.referralTo}
Patient ID: ${referral.patientId}
Urgency: ${referral.urgency}
Reason: ${referral.reason}

Clinical Summary:
${referral.clinicalSummary}

Symptoms:
- ${referral.symptoms.join('\n- ')}

Status: ${referral.status}
Created At: ${new Date(referral.createdAt).toLocaleString()}`;

  const handleCopy = () => {
    navigator.clipboard.writeText(fullReferralText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    const blob = new Blob([fullReferralText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `Referral_${referral.patientId}_${new Date().toISOString().split('T')[0]}.txt`;
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
                <IconUsers className="w-6 h-6 text-indigo-400 mr-3" />
                <h2 className="text-lg font-semibold text-white">Referral Details</h2>
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
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <h3 className="text-xs font-medium text-neutral-500 mb-0.5">Referral To</h3>
                    <p className="text-sm text-neutral-200 font-semibold">{referral.referralTo}</p>
                  </div>
                  <div>
                    <h3 className="text-xs font-medium text-neutral-500 mb-0.5">Patient ID</h3>
                    <p className="text-sm text-neutral-300">{referral.patientId}</p>
                  </div>
                </div>
                 <div>
                    <h3 className="text-xs font-medium text-neutral-500 mb-0.5">Urgency</h3>
                    <p className="text-sm text-neutral-300 capitalize">{referral.urgency}</p>
                  </div>
                <div>
                  <h3 className="text-xs font-medium text-neutral-500 mb-0.5">Reason for Referral</h3>
                  <p className="text-sm text-neutral-300 bg-neutral-700/50 p-3 rounded-md">{referral.reason}</p>
                </div>
                <div>
                  <h3 className="text-xs font-medium text-neutral-500 mb-0.5">Symptoms</h3>
                  <ul className="list-disc list-inside text-sm text-neutral-300 space-y-1 bg-neutral-700/50 p-3 rounded-md">
                    {referral.symptoms.map((symptom, i) => <li key={i}>{symptom}</li>)}
                  </ul>
                </div>
                <div>
                  <h3 className="text-xs font-medium text-neutral-500 mb-0.5">Clinical Summary</h3>
                  <p className="text-sm text-neutral-300 whitespace-pre-wrap bg-neutral-700/50 p-3 rounded-md">{referral.clinicalSummary}</p>
                </div>
                 <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
                    <div>
                        <h3 className="text-xs font-medium text-neutral-500 mb-0.5">Status</h3>
                        <p className="text-sm text-neutral-300 capitalize px-2 py-1 bg-neutral-700 inline-block rounded-md">{referral.status}</p>
                    </div>
                    <div>
                        <h3 className="text-xs font-medium text-neutral-500 mb-0.5">Created At</h3>
                        <p className="text-sm text-neutral-300">{new Date(referral.createdAt).toLocaleString()}</p>
                    </div>
                </div>
              </div>
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
                className="w-full sm:w-auto px-4 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg transition-colors flex items-center justify-center text-sm font-medium"
              >
                <IconDownload className="w-4 h-4 mr-2" />
                Download .txt
              </button>
              {/* <button
                onClick={() => alert('Send referral action (not implemented)')}
                className="w-full sm:w-auto px-4 py-2.5 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors flex items-center justify-center text-sm font-medium"
              >
                <IconSend className="w-4 h-4 mr-2" />
                Send Referral (Mock)
              </button> */}
            </footer>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default ReferralModal; 
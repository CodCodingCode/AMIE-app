'use client';

import React from 'react';
import { Referral } from '../chat/chatService';

interface UltraSimpleReferralModalProps {
  isOpen: boolean;
  onClose: () => void;
  referral: Referral | null;
}

const UltraSimpleReferralModal: React.FC<UltraSimpleReferralModalProps> = ({ 
  isOpen, 
  onClose, 
  referral 
}) => {
  const [copied, setCopied] = React.useState(false);

  if (!isOpen || !referral) return null;

  const fullText = 
`Referral To: ${referral.referralTo}
Patient ID: ${referral.patientId}
Urgency: ${referral.urgency}
Reason: ${referral.reason}

Clinical Summary:
${referral.clinicalSummary}

Symptoms:
- ${referral.symptoms.join('\n- ')}

Status: ${referral.status}
Created: ${new Date(referral.createdAt).toLocaleString()}`;

  const handleCopy = () => {
    navigator.clipboard.writeText(fullText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    const blob = new Blob([fullText], { type: 'text/plain' });
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
    <div 
      className="fixed inset-0 bg-smokyBlack bg-opacity-90 flex items-center justify-center p-6 z-50"
      onClick={onClose}
    >
      <div 
        className="bg-white w-full max-w-2xl max-h-[90vh] overflow-hidden rounded-xl shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="p-6 border-b border-gray-100 flex items-center justify-between">
          <h2 className="text-xl font-medium text-dukeBlue">Referral Details</h2>
          <button 
            onClick={onClose}
            className="text-mountbattenPink hover:text-dukeBlue text-2xl w-8 h-8 flex items-center justify-center rounded-full hover:bg-gray-100 transition-all"
          >
            ×
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[60vh]">
          <div className="space-y-6">
            <div className="grid grid-cols-2 gap-6">
              <div>
                <h3 className="text-sm font-medium text-dukeBlue mb-2">Referral To</h3>
                <p className="text-sm text-dukeBlue bg-gray-50 p-3 rounded-lg">{referral.referralTo}</p>
              </div>
              <div>
                <h3 className="text-sm font-medium text-dukeBlue mb-2">Patient ID</h3>
                <p className="text-sm text-dukeBlue bg-gray-50 p-3 rounded-lg">{referral.patientId}</p>
              </div>
            </div>
            
            <div>
              <h3 className="text-sm font-medium text-dukeBlue mb-2">Urgency</h3>
              <span className="inline-block px-4 py-2 text-sm bg-gray-50 text-dukeBlue border rounded-lg">
                {referral.urgency}
              </span>
            </div>
            
            <div>
              <h3 className="text-sm font-medium text-dukeBlue mb-3">Reason for Referral</h3>
              <div className="bg-gray-50 p-4 text-sm text-dukeBlue rounded-lg border">
                {referral.reason}
              </div>
            </div>
            
            <div>
              <h3 className="text-sm font-medium text-dukeBlue mb-3">Symptoms</h3>
              <div className="bg-gray-50 p-4 text-sm text-dukeBlue rounded-lg border">
                <ul className="space-y-2">
                  {referral.symptoms.map((symptom, i) => (
                    <li key={i} className="flex items-start">
                      <span className="text-dukeBlue mr-2">•</span>
                      <span>{symptom}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
            
            <div>
              <h3 className="text-sm font-medium text-dukeBlue mb-3">Clinical Summary</h3>
              <div className="bg-gray-50 p-4 text-sm text-dukeBlue rounded-lg border">
                {referral.clinicalSummary}
              </div>
            </div>
            
            <div className="grid grid-cols-2 gap-6">
              <div>
                <h3 className="text-sm font-medium text-dukeBlue mb-2">Status</h3>
                <span className="inline-block px-4 py-2 text-sm bg-gray-50 text-dukeBlue border rounded-lg">
                  {referral.status}
                </span>
              </div>
              <div>
                <h3 className="text-sm font-medium text-dukeBlue mb-2">Created</h3>
                <p className="text-sm text-dukeBlue bg-gray-50 p-3 rounded-lg">
                  {new Date(referral.createdAt).toLocaleString()}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-6 border-t border-gray-100 flex justify-end gap-4">
          <button
            onClick={handleCopy}
            className="px-6 py-3 bg-gray-50 text-dukeBlue text-sm rounded-lg border hover:bg-gray-100 transition-all"
          >
            {copied ? 'Copied!' : 'Copy'}
          </button>
          <button
            onClick={handleDownload}
            className="px-6 py-3 bg-dukeBlue text-white text-sm rounded-lg hover:opacity-80 transition-opacity"
          >
            Download
          </button>
        </div>
      </div>
    </div>
  );
};

export default UltraSimpleReferralModal;
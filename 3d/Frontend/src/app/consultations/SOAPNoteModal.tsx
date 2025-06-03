'use client';

import React from 'react';
import { SOAPNote } from '../chat/chatService';

interface UltraSimpleSOAPModalProps {
  isOpen: boolean;
  onClose: () => void;
  soapNote: SOAPNote | null;
}

const UltraSimpleSOAPModal: React.FC<UltraSimpleSOAPModalProps> = ({ 
  isOpen, 
  onClose, 
  soapNote 
}) => {
  const [copied, setCopied] = React.useState(false);

  if (!isOpen || !soapNote) return null;

  const fullText = `Subjective:\n${soapNote.subjective}\n\nObjective:\n${soapNote.objective}\n\nAssessment:\n${soapNote.assessment}\n\nPlan:\n- ${soapNote.plan.join('\n- ')}`;

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
    a.download = `SOAP_Note_${new Date().toISOString().split('T')[0]}.txt`;
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
          <h2 className="text-xl font-medium text-dukeBlue">SOAP Note</h2>
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
            <div>
              <h3 className="text-sm font-medium text-dukeBlue mb-3">Subjective</h3>
              <div className="bg-gray-50 p-4 text-sm text-dukeBlue rounded-lg border">
                {soapNote.subjective || 'N/A'}
              </div>
            </div>
            
            <div>
              <h3 className="text-sm font-medium text-dukeBlue mb-3">Objective</h3>
              <div className="bg-gray-50 p-4 text-sm text-dukeBlue rounded-lg border">
                {soapNote.objective || 'N/A'}
              </div>
            </div>
            
            <div>
              <h3 className="text-sm font-medium text-dukeBlue mb-3">Assessment</h3>
              <div className="bg-gray-50 p-4 text-sm text-dukeBlue rounded-lg border">
                {soapNote.assessment || 'N/A'}
              </div>
            </div>
            
            <div>
              <h3 className="text-sm font-medium text-dukeBlue mb-3">Plan</h3>
              <div className="bg-gray-50 p-4 text-sm text-dukeBlue rounded-lg border">
                {soapNote.plan && soapNote.plan.length > 0 ? (
                  <ul className="space-y-2">
                    {soapNote.plan.map((item, index) => (
                      <li key={index} className="flex items-start">
                        <span className="text-dukeBlue mr-2">•</span>
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  'N/A'
                )}
              </div>
            </div>
          </div>
          
          <p className="text-xs text-mountbattenPink mt-6 text-right">
            Generated: {new Date(soapNote.generatedAt).toLocaleString()}
          </p>
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

export default UltraSimpleSOAPModal;
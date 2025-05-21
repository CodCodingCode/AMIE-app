'use client';

import React, { createContext, useState, useContext, ReactNode } from 'react';

interface EhrContextType {
  ehrSummary: string | null;
  setEhrSummary: (summary: string | null) => void;
  consumeEhrSummary: () => string | null; // To get and clear the summary
}

const EhrContext = createContext<EhrContextType | undefined>(undefined);

export const EhrProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [ehrSummary, setEhrSummaryState] = useState<string | null>(null);

  const setEhrSummary = (summary: string | null) => {
    setEhrSummaryState(summary);
  };

  const consumeEhrSummary = (): string | null => {
    const summary = ehrSummary;
    setEhrSummaryState(null); // Clear after consuming
    return summary;
  };

  return (
    <EhrContext.Provider value={{ ehrSummary, setEhrSummary, consumeEhrSummary }}>
      {children}
    </EhrContext.Provider>
  );
};

export const useEhr = (): EhrContextType => {
  const context = useContext(EhrContext);
  if (context === undefined) {
    throw new Error('useEhr must be used within an EhrProvider');
  }
  return context;
}; 
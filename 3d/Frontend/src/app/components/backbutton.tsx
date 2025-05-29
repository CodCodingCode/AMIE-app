// components/BackButton.tsx
'use client';

import { useRouter } from 'next/navigation';
import { IconArrowLeft } from '@tabler/icons-react';

export default function BackButton({ to }: { to?: string }) {
  const router = useRouter();

  const handleBack = () => {
    if (to) {
      router.push(to);
    } else {
      router.back();
    }
  };

  return (
    <button 
      onClick={handleBack}
      className="flex items-center text-mountbattenPink hover:text-dukeBlue transition-colors"
    >
      <IconArrowLeft size={20} className="mr-2" />
      <span>Back</span>
    </button>
  );
}
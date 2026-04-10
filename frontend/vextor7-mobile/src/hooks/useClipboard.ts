import * as Clipboard from 'expo-clipboard';
import { useState } from 'react';

export const useClipboard = () => {
  const [hasCopied, setHasCopied] = useState(false);

  const copyToClipboard = async (text: string) => {
    await Clipboard.setStringAsync(text);
    setHasCopied(true);
    
    // Reset status after 2 seconds
    setTimeout(() => {
      setHasCopied(false);
    }, 2000);
  };

  const fetchClipboard = async () => {
    return await Clipboard.getStringAsync();
  };

  return { copyToClipboard, fetchClipboard, hasCopied };
};
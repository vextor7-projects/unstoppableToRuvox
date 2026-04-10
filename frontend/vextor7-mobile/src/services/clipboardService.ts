import * as Clipboard from 'expo-clipboard';

export const clipboardService = {
  copy: async (text: string) => {
    await Clipboard.setStringAsync(text);
  },
  
  paste: async () => {
    return await Clipboard.getStringAsync();
  }
};
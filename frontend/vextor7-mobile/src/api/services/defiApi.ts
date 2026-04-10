import { api } from '@/api';

export const defiApi = {
  getSwapQuote: async (inputMint: string, outputMint: string, amount: string) => {
    return (await api.post('/defi/swap/quote', { input_mint: inputMint, output_mint: outputMint, amount })).data;
  },
  prepareSwap: async (quoteResponse: any) => {
    return (await api.post('/defi/swap/prepare', quoteResponse)).data;
  }
};
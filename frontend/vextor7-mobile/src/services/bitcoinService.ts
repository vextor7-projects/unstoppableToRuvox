// Uses API for data, library for signing usually. 
// Since full SPV is heavy for React Native, we rely on backend for UTXO fetching
// and use bitcoinjs-lib (if available) for signing, or WalletCore.

// Placeholder for structure, as bitcoinjs-lib requires 'buffer' polyfill in RN
import { CHAINS } from '@/constants/chains';
import axios from 'axios';

export const bitcoinService = {
  // Using Mempool.space API as standard explorer for BTC
  getBalance: async (address: string): Promise<number> => {
    try {
      const response = await axios.get(`${CHAINS.bitcoin.explorerUrl}/api/address/${address}`);
      const { chain_stats, mempool_stats } = response.data;
      return (chain_stats.funded_txo_sum - chain_stats.spent_txo_sum + mempool_stats.funded_txo_sum - mempool_stats.spent_txo_sum) / 100000000;
    } catch (e) {
      console.error(e);
      return 0;
    }
  },

  validateAddress: (address: string): boolean => {
    // Basic regex for P2PKH, P2SH, Bech32
    return /^(1|3|bc1)/.test(address); 
  }
};
import { api } from '@/api';
import { API_ROUTES } from '@/constants/apiRoutes';

export const transactionApi = {
  prepare: async (data: { from_address: string; to_address: string; amount: string; chain_id: string; token_address?: string }) => {
    return (await api.post(API_ROUTES.TRANSACTIONS.PREPARE, data)).data;
  },

  broadcast: async (txHash: string, signedTx: string) => {
    return (await api.post(API_ROUTES.TRANSACTIONS.BROADCAST, { tx_hash: txHash, signed_tx: signedTx })).data;
  },

  getStatus: async (txHash: string) => {
    return (await api.get(API_ROUTES.TRANSACTIONS.STATUS(txHash))).data;
  }
};
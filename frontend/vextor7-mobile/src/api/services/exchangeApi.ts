import { api } from '@/api';
import { API_ROUTES } from '@/constants/apiRoutes';

export const exchangeApi = {
  getInternalBalance: async () => (await api.get(API_ROUTES.EXCHANGE.BALANCE)).data,
  
  internalTransfer: async (toEmail: string, amount: string, currency: string) => {
    return (await api.post(API_ROUTES.EXCHANGE.INTERNAL_TRANSFER, { to_email: toEmail, amount, currency })).data;
  },

  getDepositAddress: async (chain: string) => {
    return (await api.post(API_ROUTES.EXCHANGE.DEPOSIT_ADDRESS, { chain })).data;
  },
  
  withdraw: async (amount: string, address: string, chain: string) => {
    return (await api.post(API_ROUTES.EXCHANGE.WITHDRAWALS, { amount, address, chain })).data;
  }
};
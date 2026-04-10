import { api } from '@/api';
import { API_ROUTES } from '@/constants/apiRoutes';

export const paymentApi = {
  createSession: async (amount: number, currency: string, description?: string) => {
    return (await api.post(API_ROUTES.PAYMENTS.SESSION, { amount, currency, description })).data;
  },

  executePayment: async (sessionId: string, encryptedData: string) => {
    return (await api.post(API_ROUTES.PAYMENTS.EXECUTE(sessionId), { encrypted_data: encryptedData })).data;
  }
};
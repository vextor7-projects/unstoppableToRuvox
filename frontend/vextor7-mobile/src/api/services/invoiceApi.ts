import { api } from '@/api';
import { API_ROUTES } from '@/constants/apiRoutes';

export const invoiceApi = {
  create: async (data: any) => (await api.post(API_ROUTES.INVOICES.ROOT, data)).data,
  getAll: async () => (await api.get(API_ROUTES.INVOICES.ROOT)).data,
  pay: async (invoiceId: string) => (await api.post(API_ROUTES.INVOICES.PAY(invoiceId))).data,
};
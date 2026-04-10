import { api } from '@/api';
import { API_ROUTES } from '@/constants/apiRoutes';

export const merchantApi = {
  register: async (businessName: string) => (await api.post(API_ROUTES.MERCHANTS.REGISTER, { business_name: businessName })).data,
  getDashboard: async () => (await api.get(API_ROUTES.MERCHANTS.DASHBOARD)).data,
  requestSettlement: async (amount: number) => (await api.post(API_ROUTES.MERCHANTS.SETTLEMENT, { amount })).data,
};
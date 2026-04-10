import { api } from '@/api';
import { API_ROUTES } from '@/constants/apiRoutes';

export const subscriptionApi = {
  create: async (data: any) => (await api.post(API_ROUTES.SUBSCRIPTIONS.ROOT, data)).data,
  approvePullPayment: async (data: any) => (await api.post(API_ROUTES.SUBSCRIPTIONS.PULL_PAYMENTS, data)).data,
};
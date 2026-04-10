import { api } from '@/api';

export const vipApi = {
  getStatus: async () => (await api.get('/vip/status')).data,
  getBenefits: async () => (await api.get('/vip/benefits')).data,
};
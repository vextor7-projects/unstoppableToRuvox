import { api } from '@/api';
import { API_ROUTES } from '@/constants/apiRoutes';

export const marketApi = {
  getCoins: async (page = 1) => (await api.get(API_ROUTES.MARKET.COINS, { params: { page } })).data,
  getChart: async (coinId: string, days = '7') => (await api.get(API_ROUTES.MARKET.CHART(coinId), { params: { days } })).data,
  createAlert: async (coinId: string, price: number) => (await api.post(API_ROUTES.MARKET.ALERTS, { coin_id: coinId, target_price: price })).data,
};
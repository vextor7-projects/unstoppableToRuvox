import { api } from '@/api';
import { API_ROUTES } from '@/constants/apiRoutes';

export const nftApi = {
  getAll: async () => (await api.get(API_ROUTES.NFTS.ROOT)).data,
  prepareTransfer: async (data: any) => (await api.post(API_ROUTES.NFTS.PREPARE_TRANSFER, data)).data,
};
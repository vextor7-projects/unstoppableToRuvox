import { api } from '@/api';
import { API_ROUTES } from '@/constants/apiRoutes';

export const stakingApi = {
  getOptions: async () => (await api.get(API_ROUTES.STAKING.OPTIONS)).data,
  stake: async (optionId: string, amount: number) => (await api.post(API_ROUTES.STAKING.STAKE, { option_id: optionId, amount })).data,
  unstake: async (positionId: string) => (await api.post(API_ROUTES.STAKING.UNSTAKE, { position_id: positionId })).data,
};
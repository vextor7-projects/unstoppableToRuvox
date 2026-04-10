import { api } from '@/api';
import { API_ROUTES } from '@/constants/apiRoutes';

export const userApi = {
  getMe: async () => {
    const response = await api.get(API_ROUTES.USERS.ME);
    return response.data;
  },

  updateMe: async (data: any) => {
    const response = await api.put(API_ROUTES.USERS.ME, data);
    return response.data;
  },

  searchUser: async (query: string) => {
    const response = await api.get(API_ROUTES.USERS.SEARCH, { params: { q: query } });
    return response.data;
  }
};
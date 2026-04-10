import { api, setTokens, clearTokens } from '@/api';
import { API_ROUTES } from '@/constants/apiRoutes';

export const authApi = {
  login: async (data: any) => {
    const response = await api.post(API_ROUTES.AUTH.LOGIN, data); // Expects FormData usually for OAuth2
    if (response.data.access_token) {
      await setTokens(response.data.access_token, response.data.refresh_token);
    }
    return response.data;
  },
  
  register: async (data: any) => {
    const response = await api.post(API_ROUTES.AUTH.REGISTER, data);
    return response.data;
  },

  logout: async () => {
    try {
      await api.post(API_ROUTES.AUTH.LOGOUT);
    } finally {
      await clearTokens();
    }
  }
};
import { api } from '@/api';
import { API_ROUTES } from '@/constants/apiRoutes';

export const walletApi = {
  getPortfolios: async () => {
    return (await api.get(API_ROUTES.WALLETS.PORTFOLIOS)).data;
  },

  createPortfolio: async (name: string) => {
    return (await api.post(API_ROUTES.WALLETS.PORTFOLIOS, { name })).data;
  },

  createWallet: async (portfolioId: string, chainId: string, address: string, publicKey: string) => {
    return (await api.post(API_ROUTES.WALLETS.ROOT, { portfolio_id: portfolioId, chain_id: chainId, address, public_key: publicKey })).data;
  },

  getBalance: async (address: string) => {
    return (await api.get(API_ROUTES.WALLETS.BALANCE(address))).data;
  },

  getHistory: async (address: string) => {
    return (await api.get(API_ROUTES.WALLETS.HISTORY(address))).data;
  }
};
import React, { createContext, useState, useEffect, ReactNode } from 'react';
import { walletApi } from '@/api/services/walletApi';
import { useAuth } from '@/hooks/useAuth';
import { Wallet, Portfolio } from '@/types/wallet';

interface WalletContextType {
  portfolios: Portfolio[];
  activePortfolio: Portfolio | null;
  activeWallet: Wallet | null;
  isLoading: boolean;
  refreshWallets: () => Promise<void>;
  selectPortfolio: (portfolioId: string) => void;
  selectWallet: (walletId: string) => void;
}

export const WalletContext = createContext<WalletContextType | undefined>(undefined);

export const WalletProvider = ({ children }: { children: ReactNode }) => {
  const { user } = useAuth();
  const [portfolios, setPortfolios] = useState<Portfolio[]>([]);
  const [activePortfolio, setActivePortfolio] = useState<Portfolio | null>(null);
  const [activeWallet, setActiveWallet] = useState<Wallet | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const refreshWallets = async () => {
    if (!user) return;
    setIsLoading(true);
    try {
      const data = await walletApi.getPortfolios();
      setPortfolios(data);
      
      // Default selection logic
      if (data.length > 0 && !activePortfolio) {
        setActivePortfolio(data[0]);
      }
    } catch (error) {
      console.error('Failed to load wallets', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (user) refreshWallets();
    else {
      setPortfolios([]);
      setActivePortfolio(null);
    }
  }, [user]);

  const selectPortfolio = (portfolioId: string) => {
    const portfolio = portfolios.find(p => p.id === portfolioId);
    if (portfolio) setActivePortfolio(portfolio);
  };

  const selectWallet = (walletId: string) => {
    if (!activePortfolio) return;
    const wallet = activePortfolio.wallets.find(w => w.id === walletId);
    if (wallet) setActiveWallet(wallet);
  };

  return (
    <WalletContext.Provider value={{
      portfolios,
      activePortfolio,
      activeWallet,
      isLoading,
      refreshWallets,
      selectPortfolio,
      selectWallet,
    }}>
      {children}
    </WalletContext.Provider>
  );
};
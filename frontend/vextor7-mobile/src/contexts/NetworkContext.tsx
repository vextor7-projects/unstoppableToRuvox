import React, { createContext, useState, useEffect, ReactNode } from 'react';
import NetInfo, { NetInfoState } from '@react-native-community/netinfo';

interface NetworkContextType {
  isConnected: boolean;
  isInternetReachable: boolean;
  type: string;
}

export const NetworkContext = createContext<NetworkContextType | undefined>(undefined);

export const NetworkProvider = ({ children }: { children: ReactNode }) => {
  const [networkState, setNetworkState] = useState<NetInfoState | null>(null);

  useEffect(() => {
    const unsubscribe = NetInfo.addEventListener((state) => {
      setNetworkState(state);
    });
    return () => unsubscribe();
  }, []);

  return (
    <NetworkContext.Provider value={{
      isConnected: networkState?.isConnected ?? true,
      isInternetReachable: networkState?.isInternetReachable ?? true,
      type: networkState?.type ?? 'unknown',
    }}>
      {children}
    </NetworkContext.Provider>
  );
};
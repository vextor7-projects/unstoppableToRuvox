// App.tsx
import 'react-native-gesture-handler'; // MUST be at the very top
import React, { useEffect } from 'react';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { Provider as ReduxProvider } from 'react-redux';
import { RootNavigator } from '@/navigation';
import { store } from '@/store';

// Context Providers
import { NetworkProvider } from '@/contexts/NetworkContext';
import { SettingsProvider } from '@/contexts/SettingsContext';
import { AuthProvider } from '@/contexts/AuthContext';
import { WalletProvider } from '@/contexts/WalletContext';

// Core Services & Libs
import { initSentry } from '@/lib/sentry';
import '@/lib/i18n';

export default function App() {
  useEffect(() => {
    // Initialize crash reporting and monitoring in production
    initSentry();
  }, []);

  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <ReduxProvider store={store}>
        <NetworkProvider>
          <SettingsProvider>
            <AuthProvider>
              <WalletProvider>
                <RootNavigator />
              </WalletProvider>
            </AuthProvider>
          </SettingsProvider>
        </NetworkProvider>
      </ReduxProvider>
    </GestureHandlerRootView>
  );
}

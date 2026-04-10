import React, { createContext, useState, useEffect, ReactNode, useContext } from 'react';
import * as SecureStore from 'expo-secure-store';
import { authApi } from '@/api/services/authApi'; // Assuming moved to api/services per instruction
import { userApi } from '@/api/services/userApi';
import { clearTokens, getAccessToken, setTokens } from '@/api';
import { useBiometrics } from '@/hooks/useBiometrics';

interface User {
  id: string;
  email: string;
  username: string;
  is_active: boolean;
  is_superuser: boolean;
  kyc_level: number;
}

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (data: any) => Promise<void>;
  register: (data: any) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
  loginWithBiometrics: () => Promise<boolean>;
}

export const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const { authenticate, isSupported } = useBiometrics();

  // Load user session on startup
  useEffect(() => {
    const loadSession = async () => {
      try {
        const token = await getAccessToken();
        if (token) {
          await refreshUser();
        }
      } catch (error) {
        console.log('No active session found');
      } finally {
        setIsLoading(false);
      }
    };
    loadSession();
  }, []);

  const refreshUser = async () => {
    try {
      const userData = await userApi.getMe();
      setUser(userData);
    } catch (error) {
      console.error('Failed to fetch user profile:', error);
      await logout(); // Invalid token state
    }
  };

  const login = async (data: any) => {
    setIsLoading(true);
    try {
      // 1. Call API
      const response = await authApi.login(data); // response contains access_token, refresh_token
      
      // 2. Persist Tokens implicitly handled by authApi or explicitly here if authApi just returns data
      // Assuming authApi helper setTokens was called or we call it here:
      // await setTokens(response.access_token, response.refresh_token);

      // 3. Store credentials securely for biometrics if needed (optional)
      if (data.password && isSupported) {
        await SecureStore.setItemAsync('biometric_secret', data.password);
        await SecureStore.setItemAsync('biometric_email', data.username || data.email);
      }

      await refreshUser();
    } catch (error) {
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const loginWithBiometrics = async (): Promise<boolean> => {
    if (!isSupported) return false;

    const email = await SecureStore.getItemAsync('biometric_email');
    const password = await SecureStore.getItemAsync('biometric_secret');

    if (!email || !password) return false;

    const authenticated = await authenticate('Login to Ruvox');
    if (authenticated) {
      await login({ username: email, password }); // Re-login to get fresh tokens
      return true;
    }
    return false;
  };

  const register = async (data: any) => {
    setIsLoading(true);
    try {
      await authApi.register(data);
      // Auto-login after register? Or redirect to verify email. 
      // For now, we assume user needs to login.
    } catch (error) {
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    try {
      await authApi.logout();
    } catch (e) {
      // Ignore network errors on logout
    } finally {
      await clearTokens();
      setUser(null);
    }
  };

  return (
    <AuthContext.Provider value={{
      user,
      isLoading,
      isAuthenticated: !!user,
      login,
      register,
      logout,
      refreshUser,
      loginWithBiometrics
    }}>
      {children}
    </AuthContext.Provider>
  );
};
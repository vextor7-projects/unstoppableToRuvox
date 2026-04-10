import React, { createContext, useState, useEffect, ReactNode } from 'react';
import { MMKV } from 'react-native-mmkv';
import { Appearance } from 'react-native';

const storage = new MMKV();

interface SettingsContextType {
  theme: 'light' | 'dark' | 'system';
  currency: string;
  language: string;
  biometricsEnabled: boolean;
  setTheme: (theme: 'light' | 'dark' | 'system') => void;
  setCurrency: (currency: string) => void;
  setLanguage: (lang: string) => void;
  toggleBiometrics: (enabled: boolean) => void;
}

export const SettingsContext = createContext<SettingsContextType | undefined>(undefined);

export const SettingsProvider = ({ children }: { children: ReactNode }) => {
  const [theme, setThemeState] = useState<'light' | 'dark' | 'system'>('system');
  const [currency, setCurrencyState] = useState('USD');
  const [language, setLanguageState] = useState('en');
  const [biometricsEnabled, setBiometricsEnabled] = useState(false);

  useEffect(() => {
    // Load Settings
    const storedTheme = storage.getString('settings.theme') as 'light' | 'dark' | 'system';
    const storedCurrency = storage.getString('settings.currency');
    const storedLang = storage.getString('settings.language');
    const storedBio = storage.getBoolean('settings.biometrics');

    if (storedTheme) setThemeState(storedTheme);
    if (storedCurrency) setCurrencyState(storedCurrency);
    if (storedLang) setLanguageState(storedLang);
    if (storedBio !== undefined) setBiometricsEnabled(storedBio);
  }, []);

  const setTheme = (newTheme: 'light' | 'dark' | 'system') => {
    setThemeState(newTheme);
    storage.set('settings.theme', newTheme);
  };

  const setCurrency = (curr: string) => {
    setCurrencyState(curr);
    storage.set('settings.currency', curr);
  };

  const setLanguage = (lang: string) => {
    setLanguageState(lang);
    storage.set('settings.language', lang);
  };

  const toggleBiometrics = (enabled: boolean) => {
    setBiometricsEnabled(enabled);
    storage.set('settings.biometrics', enabled);
  };

  return (
    <SettingsContext.Provider value={{
      theme,
      currency,
      language,
      biometricsEnabled,
      setTheme,
      setCurrency,
      setLanguage,
      toggleBiometrics
    }}>
      {children}
    </SettingsContext.Provider>
  );
};
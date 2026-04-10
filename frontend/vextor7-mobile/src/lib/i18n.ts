import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import * as Localization from 'expo-localization';
import { MMKV } from 'react-native-mmkv';

// Initialize MMKV for fast storage of user language preference
const storage = new MMKV();

// English Translations (Default)
const en = {
  common: {
    welcome: 'Welcome to Ruvox',
    loading: 'Loading...',
    error: 'An error occurred',
    retry: 'Retry',
    save: 'Save',
    cancel: 'Cancel',
    next: 'Next',
    skip: 'Skip',
    confirm: 'Confirm',
  },
  auth: {
    login: 'Login',
    register: 'Create Account',
    enterPin: 'Enter PIN',
    biometrics: 'Use Biometrics',
  },
  wallet: {
    totalBalance: 'Total Balance',
    send: 'Send',
    receive: 'Receive',
    swap: 'Swap',
    scan: 'Scan',
  },
  errors: {
    network: 'Network connection lost',
    unauthorized: 'Session expired, please login again',
  }
};

const RESOURCES = {
  en: { translation: en },
  // Add other languages here
};

const LANGUAGE_KEY = 'user-language';

const languageDetector = {
  type: 'languageDetector' as const,
  async: true,
  detect: (callback: (lang: string) => void) => {
    try {
      // 1. Check user preference in storage
      const storedLanguage = storage.getString(LANGUAGE_KEY);
      if (storedLanguage) {
        return callback(storedLanguage);
      }
      
      // 2. Check device locale
      const deviceLocale = Localization.getLocales()[0]?.languageCode;
      return callback(deviceLocale || 'en');
    } catch (e) {
      callback('en');
    }
  },
  init: () => {},
  cacheUserLanguage: (language: string) => {
    storage.set(LANGUAGE_KEY, language);
  },
};

i18n
  .use(languageDetector)
  .use(initReactI18next)
  .init({
    compatibilityJSON: 'v3',
    fallbackLng: 'en',
    resources: RESOURCES,
    interpolation: {
      escapeValue: false, // React handles XSS
    },
    react: {
      useSuspense: false,
    },
  });

export default i18n;
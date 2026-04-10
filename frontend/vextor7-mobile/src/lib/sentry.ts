import * as Sentry from 'sentry-expo';
import { Platform } from 'react-native';

export const initSentry = () => {
  if (!process.env.EXPO_PUBLIC_SENTRY_DSN) {
    console.warn('Sentry DSN not found. Skipping initialization.');
    return;
  }

  Sentry.init({
    dsn: process.env.EXPO_PUBLIC_SENTRY_DSN,
    enableInExpoDevelopment: true,
    debug: __DEV__, // If true, Sentry will try to print out useful debugging information
    tracesSampleRate: 1.0, // Capture 100% of the transactions for performance monitoring
    environment: process.env.NODE_ENV === 'production' ? 'production' : 'development',
  });
};

export const logError = (error: unknown, context?: Record<string, any>) => {
  if (__DEV__) {
    console.error(error);
  } else {
    Sentry.Native.captureException(error, {
      extra: context,
    });
  }
};
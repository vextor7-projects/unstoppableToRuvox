import * as Sentry from '@sentry/react-native';

export const initSentry = () => {
  if (!process.env.EXPO_PUBLIC_SENTRY_DSN) {
    console.warn('Sentry DSN not found. Skipping initialization.');
    return;
  }

  Sentry.init({
    dsn: process.env.EXPO_PUBLIC_SENTRY_DSN,
    // debug: __DEV__ is fine, but usually false in prod to save logs
    debug: false, 
    tracesSampleRate: 1.0,
    // The new SDK handles environment and Expo dev automatically, 
    // but you can still keep your logic if preferred.
  });
};

export const logError = (error: unknown, context?: Record<string, any>) => {
  if (__DEV__) {
    console.error('Debug Error:', error, context);
  }
  
  // Use Sentry.captureException directly (Sentry.Native is deprecated)
  Sentry.captureException(error, {
    extra: context,
  });
};
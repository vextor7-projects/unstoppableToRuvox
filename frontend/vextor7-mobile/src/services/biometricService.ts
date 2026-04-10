import * as LocalAuthentication from 'expo-local-authentication';

export const biometricService = {
  checkAvailability: async () => {
    const hasHardware = await LocalAuthentication.hasHardwareAsync();
    const isEnrolled = await LocalAuthentication.isEnrolledAsync();
    return hasHardware && isEnrolled;
  },

  prompt: async (message: string) => {
    const result = await LocalAuthentication.authenticateAsync({
      promptMessage: message,
      disableDeviceFallback: false,
    });
    return result.success;
  }
};
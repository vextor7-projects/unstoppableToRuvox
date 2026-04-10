import { useState, useEffect } from 'react';
import * as LocalAuthentication from 'expo-local-authentication';
import { Alert } from 'react-native';

export const useBiometrics = () => {
  const [isSupported, setIsSupported] = useState(false);
  const [biometricType, setBiometricType] = useState<LocalAuthentication.AuthenticationType | null>(null);

  useEffect(() => {
    (async () => {
      const compatible = await LocalAuthentication.hasHardwareAsync();
      setIsSupported(compatible);
      
      if (compatible) {
        const types = await LocalAuthentication.supportedAuthenticationTypesAsync();
        if (types.includes(LocalAuthentication.AuthenticationType.FACIAL_RECOGNITION)) {
          setBiometricType(LocalAuthentication.AuthenticationType.FACIAL_RECOGNITION);
        } else if (types.includes(LocalAuthentication.AuthenticationType.FINGERPRINT)) {
          setBiometricType(LocalAuthentication.AuthenticationType.FINGERPRINT);
        }
      }
    })();
  }, []);

  const authenticate = async (reason = 'Authenticate to access your wallet'): Promise<boolean> => {
    if (!isSupported) {
      Alert.alert('Not Supported', 'Biometric authentication is not available on this device.');
      return false;
    }

    const result = await LocalAuthentication.authenticateAsync({
      promptMessage: reason,
      fallbackLabel: 'Use PIN',
    });

    return result.success;
  };

  return { isSupported, biometricType, authenticate };
};
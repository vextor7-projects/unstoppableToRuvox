import React from 'react';
import { TouchableOpacity, StyleSheet } from 'react-native';
import { theme } from '@/styles/theme';
import { Icon } from '@/components/common/Icon';
import { Typography } from '@/components/common/Typography';
import { useBiometrics } from '@/hooks/useBiometrics';
import { LocalAuthentication } from 'expo-local-authentication';

interface BiometricButtonProps {
  onAuthenticate: () => void;
}

export const BiometricButton: React.FC<BiometricButtonProps> = ({ onAuthenticate }) => {
  const { isSupported, biometricType } = useBiometrics();

  if (!isSupported) return null;

  const iconName = biometricType === 1 
    ? 'fingerprint'
    : 'maximize'; 

  return (
    <TouchableOpacity style={styles.container} onPress={onAuthenticate}>
      <Icon name={iconName} size={32} color={theme.colors.primary} />
      <Typography variant="caption" color={theme.colors.primary} style={{ marginTop: 4 }}>
        {biometricType === 1 ? 'Touch ID' : 'Face ID'}
      </Typography>
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    justifyContent: 'center',
    padding: theme.spacing.m,
  },
});
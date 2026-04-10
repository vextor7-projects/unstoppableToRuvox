import React from 'react';
import { View, StyleSheet } from 'react-native';
import QRCode from 'react-native-qrcode-svg';
import { theme } from '@/styles/theme';

interface QrCodeDisplayProps {
  value: string;
  size?: number;
  logo?: any; // Image source
}

export const QrCodeDisplay: React.FC<QrCodeDisplayProps> = ({ 
  value, 
  size = 200, 
  logo 
}) => {
  return (
    <View style={styles.container}>
      <View style={styles.qrWrapper}>
        <QRCode
          value={value}
          size={size}
          color="black" // QR codes scan best black on white
          backgroundColor="white"
          logo={logo}
          logoSize={size * 0.2}
          logoBackgroundColor='white'
          logoMargin={2}
        />
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    justifyContent: 'center',
    marginVertical: theme.spacing.l,
  },
  qrWrapper: {
    padding: theme.spacing.l,
    backgroundColor: 'white',
    borderRadius: theme.borderRadius.xl,
    // Add glow effect for the "Cyberpunk" feel around the white box
    shadowColor: theme.colors.primary,
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.5,
    shadowRadius: 20,
    elevation: 10,
  },
});
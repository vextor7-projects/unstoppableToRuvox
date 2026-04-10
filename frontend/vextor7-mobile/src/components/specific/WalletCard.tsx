import React from 'react';
import { View, StyleSheet, TouchableOpacity, ViewStyle } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { theme } from '@/styles/theme';
import { Typography } from '@/components/common/Typography';
import { Icon } from '@/components/common/Icon';
import { useClipboard } from '@/hooks/useClipboard';
import { formatCurrency, shortenAddress } from '@/utils/helpers';
import { Wallet } from '@/types/wallet';

interface WalletCardProps {
  wallet: Wallet | null; // Allow null for loading/empty state
  onPress?: () => void;
  style?: ViewStyle;
}

export const WalletCard: React.FC<WalletCardProps> = ({ wallet, onPress, style }) => {
  const { copyToClipboard, hasCopied } = useClipboard();

  const handleCopy = () => {
    if (wallet?.address) {
      copyToClipboard(wallet.address);
    }
  };

  if (!wallet) {
    // Skeleton / Empty State
    return (
      <View style={[styles.container, styles.skeleton, style]}>
        <Typography variant="h3" color={theme.colors.textSecondary}>
          No Wallet Selected
        </Typography>
      </View>
    );
  }

  return (
    <TouchableOpacity activeOpacity={0.9} onPress={onPress} style={[styles.wrapper, style]}>
      <LinearGradient
        colors={theme.colors.gradients.primary}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
        style={styles.container}
      >
        <View style={styles.header}>
          <Typography variant="label" color={theme.colors.textInverse} style={{ opacity: 0.8 }}>
            {wallet.name}
          </Typography>
          <View style={styles.badge}>
            <Typography variant="caption" color={theme.colors.textInverse} weight="bold">
              {wallet.chainId.toUpperCase()}
            </Typography>
          </View>
        </View>

        <View style={styles.balanceContainer}>
          <Typography variant="h1" color={theme.colors.textInverse}>
            {formatCurrency(wallet.totalValueUsd)}
          </Typography>
        </View>

        <View style={styles.footer}>
          <TouchableOpacity 
            style={styles.addressContainer} 
            onPress={handleCopy}
            activeOpacity={0.7}
          >
            <Typography variant="caption" color={theme.colors.textInverse} style={{ opacity: 0.9, marginRight: 6 }}>
              {shortenAddress(wallet.address)}
            </Typography>
            <Icon 
              name={hasCopied ? 'check' : 'copy'} 
              size={14} 
              color={theme.colors.textInverse} 
            />
          </TouchableOpacity>
        </View>
      </LinearGradient>
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  wrapper: {
    shadowColor: theme.colors.primary,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 5,
  },
  container: {
    borderRadius: theme.borderRadius.xl,
    padding: theme.spacing.l,
    height: 180,
    justifyContent: 'space-between',
  },
  skeleton: {
    backgroundColor: theme.colors.backgroundSecondary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  badge: {
    backgroundColor: 'rgba(255,255,255,0.2)',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 4,
  },
  balanceContainer: {
    flex: 1,
    justifyContent: 'center',
  },
  footer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  addressContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(0,0,0,0.1)',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
});
import React from 'react';
import { View, StyleSheet, TouchableOpacity, Image } from 'react-native';
import { theme } from '@/styles/theme';
import { Typography } from '@/components/common/Typography';
import { Token } from '@/types/wallet';
import { formatCurrency, formatCrypto } from '@/utils/helpers';

interface AssetRowProps {
  token: Token;
  onPress: (token: Token) => void;
}

export const AssetRow: React.FC<AssetRowProps> = ({ token, onPress }) => {
  const isPositive = (token.priceUsd || 0) >= 0; // Simplified logic, real app checks 24h change

  return (
    <TouchableOpacity style={styles.container} onPress={() => onPress(token)}>
      <View style={styles.left}>
        {token.logoURI ? (
          <Image source={{ uri: token.logoURI }} style={styles.logo} />
        ) : (
          <View style={[styles.logo, { backgroundColor: theme.colors.backgroundTertiary }]} />
        )}
        <View>
          <Typography variant="body" weight="bold">{token.symbol}</Typography>
          <Typography variant="caption" color={theme.colors.textSecondary}>
            {token.name}
          </Typography>
        </View>
      </View>

      <View style={styles.right}>
        <Typography variant="body" weight="bold">
          {formatCurrency(token.valueUsd)}
        </Typography>
        <Typography variant="caption" color={theme.colors.textSecondary}>
          {formatCrypto(token.balanceFormatted, '')}
        </Typography>
      </View>
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: theme.spacing.m,
    backgroundColor: theme.colors.backgroundSecondary,
    marginBottom: theme.spacing.s,
    borderRadius: theme.borderRadius.l,
  },
  left: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  right: {
    alignItems: 'flex-end',
  },
  logo: {
    width: 40,
    height: 40,
    borderRadius: 20,
    marginRight: theme.spacing.m,
  },
});
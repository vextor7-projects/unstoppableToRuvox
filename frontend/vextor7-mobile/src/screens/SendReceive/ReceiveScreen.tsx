import React, { useState } from 'react';
import { View, StyleSheet, TouchableOpacity } from 'react-native';
import { useRoute, useNavigation, RouteProp } from '@react-navigation/native';
import * as Sharing from 'expo-sharing';
import { SafeAreaViewWrapper } from '@/components/layout/SafeAreaViewWrapper';
import { Header } from '@/components/layout/Header';
import { Container } from '@/components/layout/Container';
import { Typography } from '@/components/common/Typography';
import { Button } from '@/components/common/Button';
import { Icon } from '@/components/common/Icon';
import { QrCodeDisplay } from '@/components/specific/QrCodeDisplay';
import { theme } from '@/styles/theme';
import { useWallets } from '@/hooks/useWallets';
import { useClipboard } from '@/hooks/useClipboard';
import { WalletStackParamList } from '@/types/navigation';

type ReceiveScreenRouteProp = RouteProp<WalletStackParamList, 'Receive'>;

export default function ReceiveScreen() {
  const route = useRoute<ReceiveScreenRouteProp>();
  const navigation = useNavigation();
  const { walletId, token } = route.params;
  const { activePortfolio } = useWallets();
  const { copyToClipboard, hasCopied } = useClipboard();

  const wallet = activePortfolio?.wallets.find(w => w.id === walletId);
  const address = wallet?.address || 'Loading...';
  const network = wallet?.chainId.toUpperCase() || '';

  const handleShare = async () => {
    const isAvailable = await Sharing.isAvailableAsync();
    if (isAvailable) {
      // In production, you would capture the view as an image and share it, 
      // or share a deep link/payment URI. Sharing plain text address for now.
      await Sharing.shareAsync(`Here is my ${network} address: ${address}`);
    }
  };

  return (
    <SafeAreaViewWrapper>
      <Header title={`Receive ${token ? token.symbol : ''}`} />
      <Container scrollable centered contentContainerStyle={styles.container}>
        
        <View style={styles.warningBox}>
          <Icon name="alert-triangle" size={20} color={theme.colors.warning} />
          <Typography variant="caption" color={theme.colors.warning} style={styles.warningText}>
            Send only {token ? token.symbol : network} assets on the {network} network to this address. Sending other assets will result in permanent loss.
          </Typography>
        </View>

        <View style={styles.qrCard}>
          <QrCodeDisplay value={address} size={220} />
          
          <TouchableOpacity 
            style={styles.addressPill}
            activeOpacity={0.7}
            onPress={() => copyToClipboard(address)}
          >
            <Typography variant="body" weight="medium" style={styles.addressText} numberOfLines={1} ellipsizeMode="middle">
              {address}
            </Typography>
            <Icon name={hasCopied ? "check" : "copy"} size={18} color={theme.colors.primary} />
          </TouchableOpacity>
        </View>

        <View style={styles.actionRow}>
          <Button 
            title={hasCopied ? "Copied!" : "Copy Address"} 
            variant="outline"
            icon="copy"
            style={styles.actionButton}
            onPress={() => copyToClipboard(address)} 
          />
          <Button 
            title="Share" 
            variant="primary"
            icon="share-2"
            style={styles.actionButton}
            onPress={handleShare} 
          />
        </View>
      </Container>
    </SafeAreaViewWrapper>
  );
}

const styles = StyleSheet.create({
  container: { paddingBottom: theme.spacing.xxl, paddingTop: theme.spacing.xl },
  warningBox: { flexDirection: 'row', backgroundColor: 'rgba(255, 215, 0, 0.1)', padding: theme.spacing.m, borderRadius: theme.borderRadius.m, marginBottom: theme.spacing.xl, alignItems: 'center' },
  warningText: { flex: 1, marginLeft: theme.spacing.s, lineHeight: 18 },
  qrCard: { backgroundColor: theme.colors.backgroundSecondary, borderRadius: theme.borderRadius.xl, padding: theme.spacing.xl, alignItems: 'center', width: '100%', marginBottom: theme.spacing.xl },
  addressPill: { flexDirection: 'row', alignItems: 'center', backgroundColor: theme.colors.backgroundTertiary, paddingHorizontal: theme.spacing.m, paddingVertical: theme.spacing.m, borderRadius: theme.borderRadius.m, marginTop: theme.spacing.l, width: '100%' },
  addressText: { flex: 1, marginRight: theme.spacing.s },
  actionRow: { flexDirection: 'row', justifyContent: 'space-between', gap: theme.spacing.m, width: '100%' },
  actionButton: { flex: 1 },
});
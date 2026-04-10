import React, { useEffect, useState } from 'react';
import { View, StyleSheet, FlatList, RefreshControl, TouchableOpacity } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { SafeAreaViewWrapper } from '@/components/layout/SafeAreaViewWrapper';
import { WalletCard } from '@/components/specific/WalletCard';
import { AssetRow } from '@/components/specific/AssetRow';
import { TransactionItem } from '@/components/specific/TransactionItem';
import { Typography } from '@/components/common/Typography';
import { Icon } from '@/components/common/Icon';
import { theme } from '@/styles/theme';
import { useWallets } from '@/hooks/useWallets';
import { Token, Transaction } from '@/types/wallet';

// Mock Quick Actions
const ACTIONS = [
  { id: 'receive', title: 'Receive', icon: 'arrow-down' as const },
  { id: 'send', title: 'Send', icon: 'arrow-up' as const },
  { id: 'swap', title: 'Swap', icon: 'repeat' as const },
  { id: 'scan', title: 'Scan', icon: 'maximize' as const },
];

export default function WalletHomeScreen() {
  const navigation = useNavigation<any>();
  const { activePortfolio, activeWallet, refreshWallets, isLoading } = useWallets();
  const [refreshing, setRefreshing] = useState(false);

  // Initial fetch
  useEffect(() => {
    refreshWallets();
  }, []);

  const onRefresh = async () => {
    setRefreshing(true);
    await refreshWallets();
    setRefreshing(false);
  };

  const handleAction = (id: string) => {
    if (id === 'receive') navigation.navigate('Receive', { walletId: activeWallet?.id });
    if (id === 'send') navigation.navigate('Send', { walletId: activeWallet?.id });
    if (id === 'swap') navigation.navigate('SwapTab');
    if (id === 'scan') navigation.navigate('PayTab'); // Assuming PayTab has scanner
  };

  const renderHeader = () => (
    <View>
      <View style={styles.header}>
        <View style={styles.userInfo}>
          <View style={styles.avatar}><Icon name="user" color="#fff" size={20} /></View>
          <Typography variant="h3" weight="bold">Ruvox</Typography>
        </View>
        <Icon name="bell" size={24} color={theme.colors.textPrimary} />
      </View>

      <WalletCard wallet={activeWallet} style={{ marginHorizontal: theme.spacing.m }} />

      <View style={styles.actionsRow}>
        {ACTIONS.map((action) => (
            <View key={action.id} style={styles.actionItem}>
            <TouchableOpacity 
                style={styles.actionButton}
                activeOpacity={0.7}
                onPress={() => handleAction(action.id)}
            >
                <Icon name={action.icon} size={24} color={theme.colors.primary} />
            </TouchableOpacity>
            <Typography variant="caption">{action.title}</Typography>
            </View>
        ))}
      </View>

      <View style={styles.sectionHeader}>
        <Typography variant="h2" weight="bold">Assets</Typography>
        <Typography variant="caption" color={theme.colors.primary}>View All</Typography>
      </View>
    </View>
  );

  return (
    <SafeAreaViewWrapper isRoot>
      <FlatList
        data={activeWallet?.tokens || []}
        keyExtractor={(item: Token) => item.address}
        ListHeaderComponent={renderHeader}
        renderItem={({ item }) => (
          <View style={{ paddingHorizontal: theme.spacing.m }}>
            <AssetRow 
              token={item} 
              onPress={(token) => navigation.navigate('AssetDetails', { token, walletId: activeWallet?.id })} 
            />
          </View>
        )}
        ListFooterComponent={() => (
          <View style={styles.footerSpace} />
        )}
        refreshControl={<RefreshControl refreshing={refreshing || isLoading} onRefresh={onRefresh} tintColor={theme.colors.primary} />}
        showsVerticalScrollIndicator={false}
      />
    </SafeAreaViewWrapper>
  );
}

const styles = StyleSheet.create({
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', padding: theme.spacing.m, marginBottom: theme.spacing.s },
  userInfo: { flexDirection: 'row', alignItems: 'center' },
  avatar: { width: 32, height: 32, borderRadius: 16, backgroundColor: theme.colors.primary, alignItems: 'center', justifyContent: 'center', marginRight: theme.spacing.s },
  actionsRow: { flexDirection: 'row', justifyContent: 'space-around', marginVertical: theme.spacing.xl, paddingHorizontal: theme.spacing.m },
  actionItem: { alignItems: 'center', gap: theme.spacing.s },
  actionButton: { width: 56, height: 56, borderRadius: 28, backgroundColor: theme.colors.backgroundTertiary, alignItems: 'center', justifyContent: 'center' },
  sectionHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingHorizontal: theme.spacing.m, marginBottom: theme.spacing.m },
  footerSpace: { height: 100 },
});
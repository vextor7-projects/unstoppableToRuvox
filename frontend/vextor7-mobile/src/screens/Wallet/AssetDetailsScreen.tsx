import React, { useEffect, useState } from 'react';
import { View, StyleSheet, FlatList, ActivityIndicator } from 'react-native';
import { useRoute, useNavigation, RouteProp } from '@react-navigation/native';
import { SafeAreaViewWrapper } from '@/components/layout/SafeAreaViewWrapper';
import { Header } from '@/components/layout/Header';
import { Typography } from '@/components/common/Typography';
import { Button } from '@/components/common/Button';
import { TransactionItem } from '@/components/specific/TransactionItem';
import { theme } from '@/styles/theme';
import { WalletStackParamList } from '@/types/navigation';
import { formatCurrency, formatCrypto } from '@/utils/helpers';
import { walletApi } from '@/api/services/walletApi';
import { Transaction } from '@/types/wallet';

type AssetDetailsRouteProp = RouteProp<WalletStackParamList, 'AssetDetails'>;

export default function AssetDetailsScreen() {
  const route = useRoute<AssetDetailsRouteProp>();
  const navigation = useNavigation<any>();
  const { token, walletId } = route.params;

  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loadingTx, setLoadingTx] = useState(true);

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        // In reality, pass the token address to filter
        const history = await walletApi.getHistory(walletId);
        setTransactions(history.items || []); 
      } catch (error) {
        console.error(error);
      } finally {
        setLoadingTx(false);
      }
    };
    fetchHistory();
  }, [walletId]);

  const renderHeader = () => (
    <View style={styles.headerContent}>
      <Typography variant="body" color={theme.colors.textSecondary}>{token.name} Balance</Typography>
      <Typography variant="price" style={styles.balance}>{formatCrypto(token.balanceFormatted, token.symbol)}</Typography>
      <Typography variant="h3" color={theme.colors.textSecondary}>~ {formatCurrency(token.valueUsd)}</Typography>
      
      {/* Action Buttons */}
      <View style={styles.actionRow}>
        <Button 
          title="Send" 
          variant="outline" 
          style={styles.actionBtn} 
          onPress={() => navigation.navigate('Send', { walletId, preSelectedToken: token })} 
        />
        <Button 
          title="Receive" 
          style={styles.actionBtn} 
          onPress={() => navigation.navigate('Receive', { walletId, token })} 
        />
      </View>

      <Typography variant="h2" weight="bold" style={styles.historyTitle}>History</Typography>
    </View>
  );

  return (
    <SafeAreaViewWrapper>
      <Header title={token.symbol} />
      <FlatList
        data={transactions}
        keyExtractor={(item) => item.id}
        ListHeaderComponent={renderHeader}
        contentContainerStyle={styles.listContent}
        showsVerticalScrollIndicator={false}
        ListEmptyComponent={() => (
          <View style={styles.emptyState}>
            {loadingTx ? <ActivityIndicator color={theme.colors.primary} /> : <Typography color={theme.colors.textSecondary}>No transactions yet</Typography>}
          </View>
        )}
        renderItem={({ item }) => (
          <TransactionItem transaction={item} onPress={(tx) => console.log('Tx details', tx)} />
        )}
      />
    </SafeAreaViewWrapper>
  );
}

const styles = StyleSheet.create({
  listContent: { paddingHorizontal: theme.spacing.m, paddingBottom: theme.spacing.xxl },
  headerContent: { alignItems: 'center', marginVertical: theme.spacing.xl },
  balance: { marginVertical: theme.spacing.s },
  actionRow: { flexDirection: 'row', justifyContent: 'center', gap: theme.spacing.m, marginTop: theme.spacing.xl, marginBottom: theme.spacing.xl * 2, width: '100%' },
  actionBtn: { flex: 1 },
  historyTitle: { alignSelf: 'flex-start', marginBottom: theme.spacing.m },
  emptyState: { alignItems: 'center', marginTop: theme.spacing.xl },
});
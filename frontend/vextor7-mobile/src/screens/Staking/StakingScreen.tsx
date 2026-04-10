import React, { useState, useEffect } from 'react';
import { View, StyleSheet, FlatList, TouchableOpacity, Alert, ActivityIndicator } from 'react-native';
import { SafeAreaViewWrapper } from '@/components/layout/SafeAreaViewWrapper';
import { Header } from '@/components/layout/Header';
import { Container } from '@/components/layout/Container';
import { Typography } from '@/components/common/Typography';
import { Button } from '@/components/common/Button';
import { Card } from '@/components/common/Card';
import { Input } from '@/components/common/Input';
import { theme } from '@/styles/theme';
import { formatCrypto, formatCurrency } from '@/utils/helpers';
import { stakingApi } from '@/api/services/stakingApi';
import { useWallets } from '@/hooks/useWallets';
import * as LocalAuthentication from 'expo-local-authentication';

interface StakePosition {
  id: string;
  amount: number;
  reward_earned: number;
  status: 'active' | 'cooling_down' | 'withdrawable';
  unlock_date?: string;
}

export default function StakingScreen() {
  const { activeWallet } = useWallets();
  const [activeTab, setActiveTab] = useState<'stake' | 'positions'>('stake');
  const [amountToStake, setAmountToStake] = useState('');
  const [positions, setPositions] = useState<StakePosition[]>([]);
  const [loading, setLoading] = useState(false);
  const [processing, setProcessing] = useState(false);

  const availableSol = activeWallet?.tokens.find(t => t.symbol === 'SOL')?.balanceFormatted || 0;
  const currentApy = 7.42; // This would typically come from an API endpoint

  useEffect(() => {
    fetchPositions();
  }, []);

  const fetchPositions = async () => {
    setLoading(true);
    try {
      const data = await stakingApi.getOptions(); // Assuming this returns user's active positions as well or we call a separate endpoint
      setPositions(data.positions || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleStake = async () => {
    if (!amountToStake || isNaN(Number(amountToStake)) || Number(amountToStake) <= 0) {
      Alert.alert('Invalid Amount', 'Please enter a valid amount to stake.');
      return;
    }

    try {
      setProcessing(true);
      const auth = await LocalAuthentication.authenticateAsync({ promptMessage: 'Authorize Staking' });
      if (!auth.success) return;

      // Real app: call stakingApi.stake() and sign tx with WalletCore
      await stakingApi.stake('sol-validator-1', Number(amountToStake));
      
      Alert.alert('Success', `Successfully staked ${amountToStake} SOL. It will begin earning rewards in the next epoch.`);
      setAmountToStake('');
      fetchPositions();
    } catch (err: any) {
      Alert.alert('Staking Failed', err.message || 'An error occurred while staking.');
    } finally {
      setProcessing(false);
    }
  };

  const handleUnstake = async (positionId: string) => {
    Alert.alert('Unstake', 'Are you sure you want to unstake? This action takes 2-3 days (one epoch) to cool down.', [
      { text: 'Cancel', style: 'cancel' },
      { 
        text: 'Unstake', 
        style: 'destructive', 
        onPress: async () => {
          setProcessing(true);
          try {
             await stakingApi.unstake(positionId);
             Alert.alert('Success', 'Unstaking initiated. Funds will be available after cooldown.');
             fetchPositions();
          } catch (e: any) {
             Alert.alert('Error', e.message);
          } finally {
             setProcessing(false);
          }
        }
      }
    ]);
  };

  const renderStakeTab = () => (
    <View style={styles.tabContent}>
      <Card variant="default" style={styles.apyCard}>
        <Typography variant="body" color={theme.colors.textSecondary}>Current SOL APY</Typography>
        <Typography variant="xxxl" weight="bold" color={theme.colors.success}>{currentApy}%</Typography>
        <Typography variant="caption" color={theme.colors.textSecondary}>Rewards auto-compound every epoch (~2.5 days)</Typography>
      </Card>

      <View style={styles.inputSection}>
        <View style={styles.balanceRow}>
          <Typography variant="label" color={theme.colors.textSecondary}>Amount to Stake</Typography>
          <Typography variant="label" color={theme.colors.primary}>Available: {formatCrypto(availableSol, 'SOL')}</Typography>
        </View>
        <Input
          value={amountToStake}
          onChangeText={setAmountToStake}
          keyboardType="decimal-pad"
          placeholder="0.00"
          rightIcon="arrow-up-right"
          onRightIconPress={() => setAmountToStake((availableSol * 0.99).toFixed(4))} // Reserve for gas
        />
      </View>

      <Button title="Stake SOL" onPress={handleStake} loading={processing} style={{ marginTop: theme.spacing.xl }} />
    </View>
  );

  const renderPositionsTab = () => (
    <FlatList
      data={positions}
      keyExtractor={(item) => item.id}
      contentContainerStyle={styles.listContent}
      ListEmptyComponent={
        loading ? <ActivityIndicator color={theme.colors.primary} /> : (
          <Typography color={theme.colors.textSecondary} align="center" style={{ marginTop: 40 }}>No active stakes.</Typography>
        )
      }
      renderItem={({ item }) => (
        <Card style={styles.positionCard}>
          <View style={styles.positionHeader}>
            <Typography variant="body" weight="bold">Staked SOL</Typography>
            <View style={[styles.statusBadge, item.status === 'active' ? styles.badgeActive : styles.badgeCooldown]}>
              <Typography variant="caption" color={item.status === 'active' ? theme.colors.success : theme.colors.warning}>
                {item.status.toUpperCase()}
              </Typography>
            </View>
          </View>
          <Typography variant="h2" weight="bold" style={{ marginVertical: theme.spacing.s }}>
            {formatCrypto(item.amount, 'SOL')}
          </Typography>
          <View style={styles.positionFooter}>
            <Typography variant="caption" color={theme.colors.textSecondary}>
              Earned: <Typography color={theme.colors.success}>+{formatCrypto(item.reward_earned, 'SOL')}</Typography>
            </Typography>
            {item.status === 'active' && (
              <TouchableOpacity onPress={() => handleUnstake(item.id)}>
                <Typography variant="button" color={theme.colors.error}>Unstake</Typography>
              </TouchableOpacity>
            )}
          </View>
        </Card>
      )}
    />
  );

  return (
    <SafeAreaViewWrapper>
      <Header title="Earn Yield" />
      <View style={styles.segmentContainer}>
        <TouchableOpacity style={[styles.segmentBtn, activeTab === 'stake' && styles.segmentActive]} onPress={() => setActiveTab('stake')}>
          <Typography color={activeTab === 'stake' ? theme.colors.textInverse : theme.colors.textSecondary} weight="bold">Stake</Typography>
        </TouchableOpacity>
        <TouchableOpacity style={[styles.segmentBtn, activeTab === 'positions' && styles.segmentActive]} onPress={() => setActiveTab('positions')}>
          <Typography color={activeTab === 'positions' ? theme.colors.textInverse : theme.colors.textSecondary} weight="bold">My Stakes</Typography>
        </TouchableOpacity>
      </View>
      <Container scrollable={activeTab === 'stake'} contentContainerStyle={styles.container}>
        {activeTab === 'stake' ? renderStakeTab() : renderPositionsTab()}
      </Container>
    </SafeAreaViewWrapper>
  );
}

const styles = StyleSheet.create({
  container: { flexGrow: 1, paddingBottom: theme.spacing.xxl },
  segmentContainer: { flexDirection: 'row', backgroundColor: theme.colors.backgroundSecondary, margin: theme.spacing.m, borderRadius: theme.borderRadius.m, padding: 4 },
  segmentBtn: { flex: 1, paddingVertical: theme.spacing.s, alignItems: 'center', borderRadius: theme.borderRadius.s },
  segmentActive: { backgroundColor: theme.colors.primary },
  tabContent: { paddingTop: theme.spacing.m },
  apyCard: { alignItems: 'center', paddingVertical: theme.spacing.xl, marginBottom: theme.spacing.xl },
  inputSection: { gap: theme.spacing.s },
  balanceRow: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 4 },
  listContent: { paddingVertical: theme.spacing.m },
  positionCard: { marginBottom: theme.spacing.m },
  positionHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  statusBadge: { paddingHorizontal: 8, paddingVertical: 4, borderRadius: 12, borderWidth: 1 },
  badgeActive: { backgroundColor: 'rgba(20, 241, 149, 0.1)', borderColor: 'rgba(20, 241, 149, 0.3)' },
  badgeCooldown: { backgroundColor: 'rgba(255, 215, 0, 0.1)', borderColor: 'rgba(255, 215, 0, 0.3)' },
  positionFooter: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginTop: theme.spacing.s, paddingTop: theme.spacing.s, borderTopWidth: 1, borderTopColor: theme.colors.divider },
});
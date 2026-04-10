import React, { useState } from 'react';
import { View, StyleSheet, TouchableOpacity, KeyboardAvoidingView, Platform, ActivityIndicator } from 'react-native';
import { SafeAreaViewWrapper } from '@/components/layout/SafeAreaViewWrapper';
import { Header } from '@/components/layout/Header';
import { Container } from '@/components/layout/Container';
import { Typography } from '@/components/common/Typography';
import { Button } from '@/components/common/Button';
import { Icon } from '@/components/common/Icon';
import { Input } from '@/components/common/Input';
import { theme } from '@/styles/theme';
import { useWallets } from '@/hooks/useWallets';

export default function SwapScreen() {
  const { activeWallet } = useWallets();
  const [payAmount, setPayAmount] = useState('');
  const [receiveAmount, setReceiveAmount] = useState('');
  const [loadingQuote, setLoadingQuote] = useState(false);

  // Mock Tokens
  const [payToken, setPayToken] = useState({ symbol: 'SOL', balance: '12.4' });
  const [receiveToken, setReceiveToken] = useState({ symbol: 'USDC', balance: '0.00' });

  // Simulate fetching a quote
  const handleAmountChange = (val: string) => {
    setPayAmount(val);
    if (!val || isNaN(Number(val))) {
      setReceiveAmount('');
      return;
    }
    setLoadingQuote(true);
    setTimeout(() => {
      setReceiveAmount((Number(val) * 145).toFixed(2)); // Mock Rate: 1 SOL = 145 USDC
      setLoadingQuote(false);
    }, 500);
  };

  const handleSwitch = () => {
    const tempT = payToken;
    setPayToken(receiveToken);
    setReceiveToken(tempT);
    setPayAmount('');
    setReceiveAmount('');
  };

  const renderSwapCard = (
    title: 'Paying' | 'Receiving', 
    amount: string, 
    token: { symbol: string, balance: string },
    onChange?: (val: string) => void,
    readOnly = false
  ) => (
    <View style={styles.card}>
      <Typography variant="label" color={theme.colors.textSecondary}>{title}</Typography>
      <View style={styles.inputRow}>
        <Input
          value={amount}
          onChangeText={onChange}
          placeholder="0.00"
          keyboardType="decimal-pad"
          editable={!readOnly}
          style={styles.amountInput}
        />
        <TouchableOpacity style={styles.tokenSelector}>
          <Typography variant="h3" weight="bold" style={{ marginRight: 4 }}>{token.symbol}</Typography>
          <Icon name="chevron-down" size={20} color={theme.colors.textPrimary} />
        </TouchableOpacity>
      </View>
      <View style={styles.balanceRow}>
        <Typography variant="caption" color={theme.colors.textSecondary}>
          Balance: {token.balance}
        </Typography>
        {title === 'Paying' && (
          <TouchableOpacity onPress={() => onChange?.(token.balance)}>
            <Typography variant="caption" color={theme.colors.primary} weight="bold">MAX</Typography>
          </TouchableOpacity>
        )}
      </View>
    </View>
  );

  return (
    <SafeAreaViewWrapper>
      <Header title="Swap" showBack={false} rightIcon="settings" onRightPress={() => {}} />
      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : 'height'} style={{ flex: 1 }}>
        <Container scrollable contentContainerStyle={styles.container}>
          
          <View style={styles.swapInterface}>
            {renderSwapCard('Paying', payAmount, payToken, handleAmountChange)}
            
            <View style={styles.switchWrapper}>
              <TouchableOpacity style={styles.switchBtn} onPress={handleSwitch} activeOpacity={0.8}>
                <Icon name="arrow-down" size={20} color={theme.colors.textPrimary} />
              </TouchableOpacity>
            </View>
            
            {renderSwapCard('Receiving', receiveAmount, receiveToken, undefined, true)}
          </View>

          {payAmount && !loadingQuote ? (
            <View style={styles.detailsContainer}>
              <View style={styles.detailRow}>
                <Typography variant="caption" color={theme.colors.textSecondary}>Rate</Typography>
                <Typography variant="caption" weight="medium">1 {payToken.symbol} = 145.00 {receiveToken.symbol}</Typography>
              </View>
              <View style={styles.detailRow}>
                <Typography variant="caption" color={theme.colors.textSecondary}>Slippage Tolerance</Typography>
                <Typography variant="caption" weight="medium">0.5%</Typography>
              </View>
              <View style={styles.detailRow}>
                <Typography variant="caption" color={theme.colors.textSecondary}>Network Fee</Typography>
                <Typography variant="caption" weight="medium">~ 0.00001 SOL</Typography>
              </View>
            </View>
          ) : loadingQuote ? (
            <ActivityIndicator style={{ marginTop: theme.spacing.xl }} color={theme.colors.primary} />
          ) : null}

          <View style={styles.footer}>
            <Button 
              title="Review Swap" 
              disabled={!payAmount || loadingQuote}
              onPress={() => console.log('Navigate to swap confirm modal')} 
            />
          </View>

        </Container>
      </KeyboardAvoidingView>
    </SafeAreaViewWrapper>
  );
}

const styles = StyleSheet.create({
  container: { paddingTop: theme.spacing.m, flexGrow: 1 },
  swapInterface: { position: 'relative' },
  card: { backgroundColor: theme.colors.backgroundSecondary, borderRadius: theme.borderRadius.l, padding: theme.spacing.l, zIndex: 1 },
  inputRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginTop: theme.spacing.s, marginBottom: theme.spacing.xs },
  amountInput: { fontSize: 32, fontWeight: '700', backgroundColor: 'transparent', borderWidth: 0, paddingHorizontal: 0, height: 50, flex: 1 },
  tokenSelector: { flexDirection: 'row', alignItems: 'center', backgroundColor: theme.colors.backgroundTertiary, paddingHorizontal: theme.spacing.m, paddingVertical: theme.spacing.s, borderRadius: theme.borderRadius.round },
  balanceRow: { flexDirection: 'row', justifyContent: 'space-between' },
  switchWrapper: { alignItems: 'center', marginVertical: -16, zIndex: 2 },
  switchBtn: { width: 40, height: 40, borderRadius: 20, backgroundColor: theme.colors.backgroundTertiary, borderWidth: 4, borderColor: theme.colors.background, alignItems: 'center', justifyContent: 'center' },
  detailsContainer: { marginTop: theme.spacing.xl, paddingHorizontal: theme.spacing.m, gap: theme.spacing.m },
  detailRow: { flexDirection: 'row', justifyContent: 'space-between' },
  footer: { marginTop: 'auto', paddingTop: theme.spacing.xxl, paddingBottom: theme.spacing.xl },
});
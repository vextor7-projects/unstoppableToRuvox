import React, { useState } from 'react';
import { View, StyleSheet, TouchableOpacity, KeyboardAvoidingView, Platform } from 'react-native';
import { useRoute, useNavigation, RouteProp } from '@react-navigation/native';
import { SafeAreaViewWrapper } from '@/components/layout/SafeAreaViewWrapper';
import { Header } from '@/components/layout/Header';
import { Container } from '@/components/layout/Container';
import { Typography } from '@/components/common/Typography';
import { Button } from '@/components/common/Button';
import { Input } from '@/components/common/Input';
import { Icon } from '@/components/common/Icon';
import { theme } from '@/styles/theme';
import { useWallets } from '@/hooks/useWallets';
import { WalletStackParamList } from '@/types/navigation';
import { transactionApi } from '@/api/services/transactionApi';
import { formatCrypto } from '@/utils/helpers';
import * as LocalAuthentication from 'expo-local-authentication';

type SendScreenRouteProp = RouteProp<WalletStackParamList, 'Send'>;
type Step = 'amount' | 'address' | 'confirm' | 'success';

export default function SendScreen() {
  const route = useRoute<SendScreenRouteProp>();
  const navigation = useNavigation<any>();
  const { walletId, preSelectedToken } = route.params;
  const { activePortfolio } = useWallets();

  const wallet = activePortfolio?.wallets.find(w => w.id === walletId);
  const token = preSelectedToken || wallet?.tokens[0]; // Fallback to first token (native)

  const [step, setStep] = useState<Step>('amount');
  const [amount, setAmount] = useState('');
  const [recipient, setRecipient] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const maxAmount = token?.balanceFormatted || 0;

  const handleNext = () => {
    setError('');
    if (step === 'amount') {
      if (!amount || isNaN(Number(amount)) || Number(amount) <= 0) {
        setError('Please enter a valid amount');
        return;
      }
      if (Number(amount) > maxAmount) {
        setError('Insufficient balance');
        return;
      }
      setStep('address');
    } else if (step === 'address') {
      if (!recipient || recipient.length < 10) {
        setError('Please enter a valid recipient address');
        return;
      }
      setStep('confirm');
    }
  };

  const handleConfirm = async () => {
    try {
      setLoading(true);
      // Biometric Auth check
      const auth = await LocalAuthentication.authenticateAsync({ promptMessage: 'Confirm Transaction' });
      if (!auth.success) {
        setLoading(false);
        return;
      }

      // API call to prepare and broadcast transaction
      if (wallet) {
        const txResponse = await transactionApi.prepare({
          from_address: wallet.address,
          to_address: recipient,
          amount: amount,
          chain_id: wallet.chainId,
          token_address: token?.address
        });
        
        // In a real flow, you sign `txResponse.unsigned_tx` with walletCoreService here
        // const signedTx = await walletCoreService.sign(..., txResponse.unsigned_tx);
        // await transactionApi.broadcast(txResponse.tx_hash, signedTx);
      }
      
      setStep('success');
    } catch (err: any) {
      setError(err.message || 'Transaction failed');
    } finally {
      setLoading(false);
    }
  };

  const renderAmountStep = () => (
    <View style={styles.stepContainer}>
      <View style={styles.balancePill}>
        <Icon name="info" size={16} color={theme.colors.textSecondary} />
        <Typography variant="label" color={theme.colors.textSecondary} style={{ marginLeft: 6 }}>
          Available: {formatCrypto(maxAmount, token?.symbol || '')}
        </Typography>
      </View>

      <View style={styles.amountInputContainer}>
        <Typography variant="h2" color={theme.colors.textSecondary}>$</Typography>
        <Input
          value={amount}
          onChangeText={(val: string) => { setAmount(val); setError(''); }}
          keyboardType="decimal-pad"
          placeholder="0.00"
          style={styles.hugeInput}
          autoFocus
        />
        <Typography variant="h2" color={theme.colors.textSecondary}>{token?.symbol}</Typography>
      </View>

      <TouchableOpacity onPress={() => setAmount(maxAmount.toString())} style={styles.maxBtn}>
        <Typography variant="button" color={theme.colors.primary}>USE MAX</Typography>
      </TouchableOpacity>
    </View>
  );

  const renderAddressStep = () => (
    <View style={styles.stepContainer}>
      <Input
        label="Recipient Address"
        placeholder={`Enter ${wallet?.chainId} address or ENS`}
        value={recipient}
        onChangeText={(val: string) => { setRecipient(val); setError(''); }}
        rightIcon="scan"
        onRightIconPress={() => navigation.navigate('PayTab')} // Navigate to scanner
        autoFocus
      />
    </View>
  );

  const renderConfirmStep = () => (
    <View style={styles.stepContainer}>
      <View style={styles.confirmCard}>
        <Typography variant="label" color={theme.colors.textSecondary}>You are sending</Typography>
        <Typography variant="h1" weight="bold" style={styles.confirmAmount}>
          {amount} {token?.symbol}
        </Typography>

        <View style={styles.divider} />

        <View style={styles.confirmRow}>
          <Typography variant="body" color={theme.colors.textSecondary}>To</Typography>
          <Typography variant="body" weight="medium" style={styles.recipientText} numberOfLines={1} ellipsizeMode="middle">
            {recipient}
          </Typography>
        </View>

        <View style={styles.confirmRow}>
          <Typography variant="body" color={theme.colors.textSecondary}>Network</Typography>
          <Typography variant="body" weight="medium" style={{ textTransform: 'capitalize' }}>
            {wallet?.chainId}
          </Typography>
        </View>

        <View style={styles.confirmRow}>
          <Typography variant="body" color={theme.colors.textSecondary}>Network Fee</Typography>
          <Typography variant="body" weight="medium">~ 0.0001 {wallet?.chainId === 'solana' ? 'SOL' : 'ETH'}</Typography>
        </View>
      </View>
    </View>
  );

  const renderSuccessStep = () => (
    <View style={[styles.stepContainer, { alignItems: 'center', justifyContent: 'center', flex: 1 }]}>
      <View style={styles.successIcon}>
        <Icon name="check" size={48} color={theme.colors.success} />
      </View>
      <Typography variant="h2" weight="bold" style={{ marginTop: theme.spacing.xl }}>Transaction Sent!</Typography>
      <Typography variant="body" color={theme.colors.textSecondary} align="center" style={{ marginTop: theme.spacing.s, marginBottom: theme.spacing.xxl }}>
        Your transaction is being processed on the {wallet?.chainId} network.
      </Typography>
      <Button title="Back to Wallet" onPress={() => navigation.popToTop()} />
    </View>
  );

  return (
    <SafeAreaViewWrapper>
      <Header 
        title={step === 'amount' ? 'Enter Amount' : step === 'address' ? 'Recipient' : step === 'confirm' ? 'Confirm' : ''} 
        showBack={step !== 'success'}
        onBack={() => {
          if (step === 'confirm') setStep('address');
          else if (step === 'address') setStep('amount');
          else navigation.goBack();
        }}
      />
      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : 'height'} style={{ flex: 1 }}>
        <Container scrollable contentContainerStyle={{ paddingVertical: theme.spacing.xl, flexGrow: 1 }}>
          
          {step === 'amount' && renderAmountStep()}
          {step === 'address' && renderAddressStep()}
          {step === 'confirm' && renderConfirmStep()}
          {step === 'success' && renderSuccessStep()}

          {error ? <Typography variant="caption" color={theme.colors.error} align="center" style={styles.errorText}>{error}</Typography> : null}

          {step !== 'success' && (
            <View style={styles.footer}>
              <Button 
                title={step === 'confirm' ? 'Confirm & Send' : 'Continue'} 
                onPress={step === 'confirm' ? handleConfirm : handleNext} 
                loading={loading}
              />
            </View>
          )}

        </Container>
      </KeyboardAvoidingView>
    </SafeAreaViewWrapper>
  );
}

const styles = StyleSheet.create({
  stepContainer: { flex: 1 },
  balancePill: { flexDirection: 'row', alignItems: 'center', alignSelf: 'center', backgroundColor: theme.colors.backgroundTertiary, paddingHorizontal: theme.spacing.m, paddingVertical: theme.spacing.s, borderRadius: theme.borderRadius.round, marginBottom: theme.spacing.xxl },
  amountInputContainer: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', paddingHorizontal: theme.spacing.l },
  hugeInput: { fontSize: 48, fontWeight: '700', textAlign: 'center', height: 80, minWidth: 150, paddingHorizontal: theme.spacing.s, backgroundColor: 'transparent', borderWidth: 0 },
  maxBtn: { alignSelf: 'center', marginTop: theme.spacing.l, padding: theme.spacing.s },
  confirmCard: { backgroundColor: theme.colors.backgroundSecondary, padding: theme.spacing.l, borderRadius: theme.borderRadius.l },
  confirmAmount: { marginVertical: theme.spacing.s, color: theme.colors.textPrimary },
  divider: { height: 1, backgroundColor: theme.colors.divider, marginVertical: theme.spacing.l },
  confirmRow: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: theme.spacing.m },
  recipientText: { flex: 1, textAlign: 'right', marginLeft: theme.spacing.xl },
  footer: { marginTop: 'auto', paddingTop: theme.spacing.xl },
  errorText: { marginBottom: theme.spacing.m },
  successIcon: { width: 96, height: 96, borderRadius: 48, backgroundColor: 'rgba(20, 241, 149, 0.1)', alignItems: 'center', justifyContent: 'center' },
});
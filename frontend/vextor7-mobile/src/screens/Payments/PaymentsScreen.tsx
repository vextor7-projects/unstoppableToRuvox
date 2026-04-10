import React, { useState } from 'react';
import { View, StyleSheet, TouchableOpacity } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { SafeAreaViewWrapper } from '@/components/layout/SafeAreaViewWrapper';
import { Header } from '@/components/layout/Header';
import { Typography } from '@/components/common/Typography';
import { Icon } from '@/components/common/Icon';
import { Button } from '@/components/common/Button';
import { theme } from '@/styles/theme';
import * as Haptics from 'expo-haptics';

export default function PaymentsScreen() {
  const navigation = useNavigation<any>();
  const [mode, setMode] = useState<'scan' | 'pos'>('pos');
  const [amount, setAmount] = useState('0.00');

  const handleKeyPress = (val: string) => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    if (val === 'backspace') {
      setAmount(prev => (prev.length > 1 ? prev.slice(0, -1) : '0.00'));
      return;
    }
    
    if (amount === '0.00') {
      setAmount(val === '.' ? '0.' : val);
    } else {
      // Prevent multiple decimals
      if (val === '.' && amount.includes('.')) return;
      // Limit to 2 decimal places
      if (amount.includes('.') && amount.split('.')[1].length >= 2) return;
      setAmount(prev => prev + val);
    }
  };

  const renderKey = (num: string) => (
    <TouchableOpacity style={styles.key} onPress={() => handleKeyPress(num)} activeOpacity={0.6}>
      <Typography variant="h2" weight="bold">{num}</Typography>
    </TouchableOpacity>
  );

  return (
    <SafeAreaViewWrapper>
      <Header title="Payments" showBack={false} />
      
      {/* Segmented Control */}
      <View style={styles.segmentContainer}>
        <TouchableOpacity 
          style={[styles.segmentBtn, mode === 'scan' && styles.segmentActive]}
          onPress={() => { setMode('scan'); navigation.navigate('ScanQR'); }}
        >
          <Typography color={mode === 'scan' ? theme.colors.textInverse : theme.colors.textSecondary} weight="bold">
            Scan QR
          </Typography>
        </TouchableOpacity>
        <TouchableOpacity 
          style={[styles.segmentBtn, mode === 'pos' && styles.segmentActive]}
          onPress={() => setMode('pos')}
        >
          <Typography color={mode === 'pos' ? theme.colors.textInverse : theme.colors.textSecondary} weight="bold">
            Merchant POS
          </Typography>
        </TouchableOpacity>
      </View>

      <View style={styles.container}>
        <View style={styles.displayContainer}>
          <Typography variant="h2" color={theme.colors.textSecondary}>$</Typography>
          <Typography variant="xxxl" weight="bold" style={styles.amountText}>{amount}</Typography>
        </View>

        <View style={styles.keypad}>
          <View style={styles.row}>{renderKey('1')}{renderKey('2')}{renderKey('3')}</View>
          <View style={styles.row}>{renderKey('4')}{renderKey('5')}{renderKey('6')}</View>
          <View style={styles.row}>{renderKey('7')}{renderKey('8')}{renderKey('9')}</View>
          <View style={styles.row}>
            {renderKey('.')}
            {renderKey('0')}
            <TouchableOpacity style={styles.key} onPress={() => handleKeyPress('backspace')}>
              <Icon name="delete" size={28} color={theme.colors.textPrimary} />
            </TouchableOpacity>
          </View>
        </View>

        <View style={styles.actionContainer}>
          <Button 
            title="Generate QR" 
            onPress={() => navigation.navigate('GenerateQR', { amount })} 
            style={{ marginBottom: theme.spacing.m }}
          />
          <TouchableOpacity style={styles.nfcButton} onPress={() => console.log('Initiate NFC')}>
            <Icon name="wifi" size={20} color={theme.colors.textSecondary} style={{ marginRight: 8, transform: [{ rotate: '90deg' }] }} />
            <Typography variant="button" color={theme.colors.textSecondary}>NFC Tap to Pay</Typography>
          </TouchableOpacity>
        </View>
      </View>
    </SafeAreaViewWrapper>
  );
}

const styles = StyleSheet.create({
  segmentContainer: { flexDirection: 'row', backgroundColor: theme.colors.backgroundSecondary, margin: theme.spacing.m, borderRadius: theme.borderRadius.m, padding: 4 },
  segmentBtn: { flex: 1, paddingVertical: theme.spacing.s, alignItems: 'center', borderRadius: theme.borderRadius.s },
  segmentActive: { backgroundColor: theme.colors.primary },
  container: { flex: 1, justifyContent: 'space-between', paddingBottom: theme.spacing.xl },
  displayContainer: { flexDirection: 'row', justifyContent: 'center', alignItems: 'center', flex: 1 },
  amountText: { fontSize: 56, marginLeft: theme.spacing.xs },
  keypad: { width: '100%', paddingHorizontal: theme.spacing.xl, gap: theme.spacing.m, marginBottom: theme.spacing.xl },
  row: { flexDirection: 'row', justifyContent: 'space-between' },
  key: { width: 80, height: 80, borderRadius: 40, backgroundColor: theme.colors.backgroundTertiary, alignItems: 'center', justifyContent: 'center' },
  actionContainer: { paddingHorizontal: theme.spacing.xl },
  nfcButton: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', paddingVertical: theme.spacing.m, borderRadius: theme.borderRadius.m, backgroundColor: 'rgba(255,255,255,0.05)', borderWidth: 1, borderColor: theme.colors.border },
});
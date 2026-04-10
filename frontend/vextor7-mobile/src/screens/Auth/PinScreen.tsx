import React, { useState } from 'react';
import { View, StyleSheet, TouchableOpacity } from 'react-native';
import { useNavigation, useRoute, RouteProp } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import * as Haptics from 'expo-haptics';
import { AuthStackParamList } from '@/types/navigation';
import { SafeAreaViewWrapper } from '@/components/layout/SafeAreaViewWrapper';
import { Header } from '@/components/layout/Header';
import { Typography } from '@/components/common/Typography';
import { PinInput } from '@/components/specific/PinInput';
import { Icon } from '@/components/common/Icon';
import { theme } from '@/styles/theme';
import { LocalStorage } from '@/utils/storage';

type PinScreenRouteProp = RouteProp<AuthStackParamList, 'PinSetup'>;

export default function PinScreen() {
  const navigation = useNavigation<NativeStackNavigationProp<AuthStackParamList>>();
  const route = useRoute<PinScreenRouteProp>();
  
  const [pin, setPin] = useState('');
  const [confirmPin, setConfirmPin] = useState('');
  const [step, setStep] = useState<'create' | 'confirm'>('create');
  const [error, setError] = useState(false);

  const handleKeyPress = async (val: string) => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    
    if (val === 'backspace') {
      if (step === 'create') setPin((prev) => prev.slice(0, -1));
      else setConfirmPin((prev) => prev.slice(0, -1));
      setError(false);
      return;
    }

    const currentVal = step === 'create' ? pin + val : confirmPin + val;
    
    if (step === 'create') {
      setPin(currentVal);
      if (currentVal.length === 6) {
        setTimeout(() => setStep('confirm'), 300);
      }
    } else {
      setConfirmPin(currentVal);
      if (currentVal.length === 6) {
        if (currentVal === pin) {
          // Success
          Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
          // Store securely in production, mapped to the user
          LocalStorage.set('user_pin', currentVal); 
          navigation.navigate('RecoveryPhrase', { mode: 'create' });
        } else {
          // Failure
          Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
          setError(true);
          setTimeout(() => {
            setConfirmPin('');
            setError(false);
          }, 500);
        }
      }
    }
  };

  const renderKey = (num: string) => (
    <TouchableOpacity 
      style={styles.key} 
      onPress={() => handleKeyPress(num)}
      activeOpacity={0.6}
    >
      <Typography variant="h2">{num}</Typography>
    </TouchableOpacity>
  );

  return (
    <SafeAreaViewWrapper>
      <Header transparent showBack onBack={() => {
        if (step === 'confirm') {
          setStep('create');
          setPin('');
          setConfirmPin('');
        } else {
          navigation.goBack();
        }
      }} />
      <View style={styles.container}>
        <View style={styles.header}>
          <Typography variant="h1" weight="bold">
            {step === 'create' ? 'Create Your PIN' : 'Confirm Your PIN'}
          </Typography>
          <Typography variant="body" color={error ? theme.colors.error : theme.colors.textSecondary} style={{ marginTop: 8 }}>
            {error ? "PINs don't match. Try again." : 'Enter a 6-digit PIN to secure your wallet'}
          </Typography>
        </View>

        <PinInput length={6} value={step === 'create' ? pin : confirmPin} />

        <View style={styles.keypad}>
          <View style={styles.row}>{renderKey('1')}{renderKey('2')}{renderKey('3')}</View>
          <View style={styles.row}>{renderKey('4')}{renderKey('5')}{renderKey('6')}</View>
          <View style={styles.row}>{renderKey('7')}{renderKey('8')}{renderKey('9')}</View>
          <View style={styles.row}>
            <View style={styles.key} /> 
            {renderKey('0')}
            <TouchableOpacity style={styles.key} onPress={() => handleKeyPress('backspace')}>
              <Icon name="delete" size={28} color={theme.colors.textPrimary} />
            </TouchableOpacity>
          </View>
        </View>
      </View>
    </SafeAreaViewWrapper>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: theme.spacing.xl, alignItems: 'center', justifyContent: 'space-between', paddingBottom: theme.spacing.xxl * 2 },
  header: { alignItems: 'center', marginTop: theme.spacing.xl },
  keypad: { width: '100%', maxWidth: 300, gap: theme.spacing.l },
  row: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: theme.spacing.l },
  key: { width: 72, height: 72, borderRadius: 36, backgroundColor: theme.colors.backgroundTertiary, alignItems: 'center', justifyContent: 'center' },
});
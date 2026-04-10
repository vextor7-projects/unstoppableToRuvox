import React, { useState, useEffect } from 'react';
import { View, StyleSheet, Switch, Alert, ActivityIndicator } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { SafeAreaViewWrapper } from '@/components/layout/SafeAreaViewWrapper';
import { Header } from '@/components/layout/Header';
import { Container } from '@/components/layout/Container';
import { Typography } from '@/components/common/Typography';
import { Button } from '@/components/common/Button';
import { Modal } from '@/components/common/Modal';
import { Input } from '@/components/common/Input';
import { QrCodeDisplay } from '@/components/specific/QrCodeDisplay';
import { theme } from '@/styles/theme';
import { useBiometrics } from '@/hooks/useBiometrics';
import { securityApi } from '@/api/services/securityApi';
import { useClipboard } from '@/hooks/useClipboard';

export default function SecurityScreen() {
  const navigation = useNavigation<any>();
  const { isSupported } = useBiometrics();
  const { copyToClipboard, hasCopied } = useClipboard();

  const [biometricsEnabled, setBiometricsEnabled] = useState(false); // Load from storage in reality
  const [totpEnabled, setTotpEnabled] = useState(false); // Should be fetched from user profile
  
  // TOTP Setup Modal State
  const [isTotpModalVisible, setIsTotpModalVisible] = useState(false);
  const [totpSecret, setTotpSecret] = useState('');
  const [totpUri, setTotpUri] = useState('');
  const [totpCode, setTotpCode] = useState('');
  const [loadingTotp, setLoadingTotp] = useState(false);

  const toggleBiometrics = () => setBiometricsEnabled(!biometricsEnabled);

  const handleEnableTotp = async () => {
    if (totpEnabled) {
      Alert.alert('Disable 2FA', 'Are you sure you want to disable Two-Factor Authentication?', [
        { text: 'Cancel', style: 'cancel' },
        { 
          text: 'Disable', 
          style: 'destructive',
          onPress: async () => {
            // In a real app, prompt for current TOTP code to disable
            setTotpEnabled(false);
          }
        }
      ]);
      return;
    }

    try {
      setLoadingTotp(true);
      setIsTotpModalVisible(true);
      const response = await securityApi.enableTotp();
      setTotpSecret(response.secret);
      setTotpUri(response.uri); // e.g., otpauth://totp/Ruvox:user@email.com?secret=...
    } catch (error) {
      Alert.alert('Error', 'Failed to initialize 2FA setup.');
      setIsTotpModalVisible(false);
    } finally {
      setLoadingTotp(false);
    }
  };

  const handleVerifyTotp = async () => {
    try {
      setLoadingTotp(true);
      await securityApi.verifyTotp(totpCode);
      setTotpEnabled(true);
      setIsTotpModalVisible(false);
      Alert.alert('Success', 'Two-Factor Authentication has been enabled.');
    } catch (error) {
      Alert.alert('Error', 'Invalid authentication code. Please try again.');
    } finally {
      setLoadingTotp(false);
    }
  };

  return (
    <SafeAreaViewWrapper>
      <Header title="Security Center" />
      <Container scrollable contentContainerStyle={styles.container}>
        
        <View style={styles.section}>
          <View style={styles.row}>
            <View>
              <Typography variant="body" weight="bold">Change PIN</Typography>
              <Typography variant="caption" color={theme.colors.textSecondary}>Update your 6-digit access code</Typography>
            </View>
            <Button 
              title="Update" 
              variant="outline" 
              onPress={() => navigation.navigate('PinSetup', { isUpdate: true })} 
              fullWidth={false}
            />
          </View>
        </View>

        {isSupported && (
          <View style={styles.section}>
            <View style={styles.row}>
              <View>
                <Typography variant="body" weight="bold">Biometric Login</Typography>
                <Typography variant="caption" color={theme.colors.textSecondary}>Use FaceID / TouchID to log in</Typography>
              </View>
              <Switch
                value={biometricsEnabled}
                onValueChange={toggleBiometrics}
                trackColor={{ false: theme.colors.border, true: theme.colors.primary }}
              />
            </View>
          </View>
        )}

        <View style={styles.section}>
          <View style={styles.row}>
            <View style={{ flex: 1, paddingRight: theme.spacing.m }}>
              <Typography variant="body" weight="bold">Two-Factor Authentication</Typography>
              <Typography variant="caption" color={theme.colors.textSecondary}>
                Secure withdrawals and login with Google Authenticator
              </Typography>
            </View>
            <Button 
              title={totpEnabled ? "Disable" : "Enable"} 
              variant={totpEnabled ? "danger" : "primary"}
              onPress={handleEnableTotp} 
              fullWidth={false}
            />
          </View>
        </View>

      </Container>

      {/* TOTP Setup Modal */}
      <Modal visible={isTotpModalVisible} onClose={() => setIsTotpModalVisible(false)} title="Setup 2FA">
        <View style={styles.modalContent}>
          {loadingTotp && !totpSecret ? (
            <ActivityIndicator size="large" color={theme.colors.primary} style={{ marginVertical: 40 }} />
          ) : (
            <>
              <Typography variant="body" color={theme.colors.textSecondary} align="center" style={{ marginBottom: theme.spacing.l }}>
                Scan this QR code with Google Authenticator or Authy.
              </Typography>

              {totpUri ? <QrCodeDisplay value={totpUri} size={200} /> : null}

              <Typography variant="caption" color={theme.colors.textTertiary} align="center" style={{ marginTop: theme.spacing.m }}>
                Or enter this code manually:
              </Typography>
              
              <View style={styles.secretBox}>
                <Typography variant="body" weight="bold" style={{ letterSpacing: 2 }}>
                  {totpSecret}
                </Typography>
                <Button 
                  title={hasCopied ? "Copied" : "Copy"} 
                  variant="ghost" 
                  onPress={() => copyToClipboard(totpSecret)} 
                  fullWidth={false}
                />
              </View>

              <Input
                placeholder="Enter 6-digit code"
                keyboardType="number-pad"
                maxLength={6}
                value={totpCode}
                onChangeText={setTotpCode}
                style={{ textAlign: 'center', fontSize: 24, letterSpacing: 5 }}
              />

              <Button 
                title="Verify & Enable" 
                onPress={handleVerifyTotp} 
                disabled={totpCode.length !== 6}
                loading={loadingTotp}
              />
            </>
          )}
        </View>
      </Modal>
    </SafeAreaViewWrapper>
  );
}

const styles = StyleSheet.create({
  container: { paddingTop: theme.spacing.m },
  section: { backgroundColor: theme.colors.backgroundSecondary, borderRadius: theme.borderRadius.l, marginBottom: theme.spacing.m, padding: theme.spacing.m },
  row: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  modalContent: { alignItems: 'center' },
  secretBox: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', backgroundColor: theme.colors.backgroundTertiary, paddingHorizontal: theme.spacing.m, paddingVertical: theme.spacing.s, borderRadius: theme.borderRadius.m, width: '100%', marginBottom: theme.spacing.xl },
});
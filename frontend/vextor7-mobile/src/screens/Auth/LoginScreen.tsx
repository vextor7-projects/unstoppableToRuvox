import React, { useState, useEffect } from 'react';
import { View, StyleSheet, KeyboardAvoidingView, Platform, Alert } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { AuthStackParamList } from '@/types/navigation';
import { SafeAreaViewWrapper } from '@/components/layout/SafeAreaViewWrapper';
import { Header } from '@/components/layout/Header';
import { Container } from '@/components/layout/Container';
import { Button } from '@/components/common/Button';
import { Input } from '@/components/common/Input';
import { Typography } from '@/components/common/Typography';
import { useAuth } from '@/hooks/useAuth';
import { useBiometrics } from '@/hooks/useBiometrics';
import { BiometricButton } from '@/components/specific/BiometricButton';
import { theme } from '@/styles/theme';

export default function LoginScreen() {
  const navigation = useNavigation<NativeStackNavigationProp<AuthStackParamList>>();
  const { login, loginWithBiometrics, isLoading } = useAuth();
  const { isSupported } = useBiometrics();
  
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleLogin = async () => {
    if (!email || !password) {
      setError('Please enter both email and password.');
      return;
    }
    setError('');
    try {
      // Backend expects OAuth2 form data typically: username and password
      await login({ username: email, password });
      // If successful, AuthContext will update and switch to MainTabNavigator automatically
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Invalid credentials. Please try again.');
    }
  };

  const handleBiometricLogin = async () => {
    try {
      const success = await loginWithBiometrics();
      if (!success) {
        Alert.alert('Authentication Failed', 'Could not verify biometrics or no saved credentials found.');
      }
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <SafeAreaViewWrapper>
      <Header title="" transparent />
      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : 'height'} style={{ flex: 1 }}>
        <Container scrollable centered>
          <View style={styles.header}>
            <Typography variant="h1" weight="bold">Welcome Back</Typography>
            <Typography variant="body" color={theme.colors.textSecondary} style={{ marginTop: 8 }}>
              Log in to your Ruvox wallet
            </Typography>
          </View>

          <View style={styles.form}>
            <Input
              label="Email"
              placeholder="your@email.com"
              keyboardType="email-address"
              autoCapitalize="none"
              value={email}
              onChangeText={(text) => { setEmail(text); setError(''); }}
            />
            <Input
              label="Password"
              placeholder="••••••••"
              secureTextEntry
              value={password}
              onChangeText={(text) => { setPassword(text); setError(''); }}
              error={error}
            />

            <Typography 
              variant="label" 
              color={theme.colors.primary} 
              align="right" 
              style={styles.forgotPassword}
            >
              Forgot Password?
            </Typography>

            <Button 
              title="Log In" 
              onPress={handleLogin} 
              loading={isLoading} 
              style={styles.loginButton} 
            />

            {isSupported && (
              <View style={styles.biometrics}>
                <Typography variant="caption" color={theme.colors.textSecondary} align="center">
                  OR
                </Typography>
                <BiometricButton onAuthenticate={handleBiometricLogin} />
              </View>
            )}
          </View>
        </Container>
      </KeyboardAvoidingView>
    </SafeAreaViewWrapper>
  );
}

const styles = StyleSheet.create({
  header: { marginBottom: theme.spacing.xxl, alignItems: 'center' },
  form: { width: '100%' },
  forgotPassword: { marginTop: -theme.spacing.s, marginBottom: theme.spacing.xl },
  loginButton: { marginBottom: theme.spacing.xl },
  biometrics: { alignItems: 'center', gap: theme.spacing.m },
});
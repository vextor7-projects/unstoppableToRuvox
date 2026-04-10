import React, { useState } from 'react';
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
import { theme } from '@/styles/theme';

export default function RegisterScreen() {
  const navigation = useNavigation<NativeStackNavigationProp<AuthStackParamList>>();
  const { register } = useAuth();
  
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSignUp = async () => {
    if (!email || !username || !password) {
      setError('All fields are required.');
      return;
    }
    if (password.length < 8) {
      setError('Password must be at least 8 characters long.');
      return;
    }
    setError('');
    setLoading(true);
    try {
      await register({ email, username, password });
      // Proceed to set up PIN code
      navigation.navigate('PinSetup', { isUpdate: false });
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Registration failed. Try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeAreaViewWrapper>
      <Header title="" transparent />
      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : 'height'} style={{ flex: 1 }}>
        <Container scrollable centered>
          <View style={styles.header}>
            <Typography variant="h1" weight="bold">Create Account</Typography>
            <Typography variant="body" color={theme.colors.textSecondary} style={{ marginTop: 8 }}>
              Join the future of Finance
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
              label="Username"
              placeholder="username"
              autoCapitalize="none"
              value={username}
              onChangeText={(text) => { setUsername(text); setError(''); }}
            />
            <Input
              label="Password"
              placeholder="••••••••"
              secureTextEntry
              value={password}
              onChangeText={(text) => { setPassword(text); setError(''); }}
              error={error}
            />

            <Button 
              title="Sign Up" 
              onPress={handleSignUp} 
              loading={loading} 
              style={styles.signupButton} 
            />
            
            <View style={styles.footer}>
              <Typography variant="body" color={theme.colors.textSecondary}>
                Already have an account?{' '}
              </Typography>
              <Typography variant="body" color={theme.colors.primary} weight="bold" onPress={() => navigation.navigate('Login')}>
                Log In
              </Typography>
            </View>
          </View>
        </Container>
      </KeyboardAvoidingView>
    </SafeAreaViewWrapper>
  );
}

const styles = StyleSheet.create({
  header: { marginBottom: theme.spacing.xxl, alignItems: 'center' },
  form: { width: '100%' },
  signupButton: { marginTop: theme.spacing.l, marginBottom: theme.spacing.xl },
  footer: { flexDirection: 'row', justifyContent: 'center' },
});
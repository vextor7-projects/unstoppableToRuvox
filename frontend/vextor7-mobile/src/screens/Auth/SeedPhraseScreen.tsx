import React, { useEffect, useState } from 'react';
import { View, StyleSheet, ActivityIndicator, Alert } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import * as ScreenCapture from 'expo-screen-capture';
import { SafeAreaViewWrapper } from '@/components/layout/SafeAreaViewWrapper';
import { Header } from '@/components/layout/Header';
import { Container } from '@/components/layout/Container';
import { Button } from '@/components/common/Button';
import { Typography } from '@/components/common/Typography';
import { walletCoreService } from '@/services/walletCoreService';
import { useClipboard } from '@/hooks/useClipboard';
import { theme } from '@/styles/theme';

export default function SeedPhraseScreen() {
  const navigation = useNavigation<any>();
  const { copyToClipboard, hasCopied } = useClipboard();
  const [mnemonic, setMnemonic] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Prevent screenshotting this sensitive screen
    ScreenCapture.preventScreenCaptureAsync();
    
    const generateWallet = async () => {
      try {
        const phrase = await walletCoreService.createMnemonic();
        setMnemonic(phrase.split(' '));
      } catch (error) {
        Alert.alert('Error', 'Failed to generate wallet. Please try again.');
      } finally {
        setLoading(false);
      }
    };

    generateWallet();

    return () => {
      ScreenCapture.allowScreenCaptureAsync();
    };
  }, []);

  const handleSaved = () => {
    // In a full flow, you would verify they saved it by asking them to input word #4, #8 etc.
    // For now, we finalize wallet creation and navigate to Main.
    navigation.reset({
      index: 0,
      routes: [{ name: 'Main' }],
    });
  };

  if (loading) {
    return (
      <SafeAreaViewWrapper>
        <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center' }}>
            <ActivityIndicator size="large" color={theme.colors.primary} />
        </View>
      </SafeAreaViewWrapper>
    );
  }

  return (
    <SafeAreaViewWrapper>
      <Header title="Backup Your Wallet" />
      <Container scrollable contentContainerStyle={styles.container}>
        <View style={styles.warningBox}>
          <Typography variant="label" color={theme.colors.warning} weight="bold">
            Do not screenshot. Anyone with these words can access your funds.
          </Typography>
        </View>

        <Typography variant="body" color={theme.colors.textSecondary} style={styles.instructions}>
          Write down these 12 words in order. Keep them safe and never share them with anyone.
        </Typography>

        <View style={styles.grid}>
          {mnemonic.map((word, index) => (
            <View key={index} style={styles.wordBox}>
              <Typography variant="caption" color={theme.colors.textTertiary} style={styles.wordNumber}>
                {index + 1}.
              </Typography>
              <Typography variant="body" weight="bold">{word}</Typography>
            </View>
          ))}
        </View>

        <Button 
          title={hasCopied ? "Copied!" : "Copy to Clipboard"} 
          variant="outline" 
          icon="copy" 
          onPress={() => copyToClipboard(mnemonic.join(' '))} 
          style={styles.copyButton}
        />

        <Button 
          title="I have saved these words" 
          onPress={handleSaved} 
        />
      </Container>
    </SafeAreaViewWrapper>
  );
}

const styles = StyleSheet.create({
  container: { paddingTop: theme.spacing.l },
  warningBox: { backgroundColor: 'rgba(255, 215, 0, 0.1)', padding: theme.spacing.m, borderRadius: theme.borderRadius.m, marginBottom: theme.spacing.m, borderWidth: 1, borderColor: 'rgba(255, 215, 0, 0.3)' },
  instructions: { marginBottom: theme.spacing.xl },
  grid: { flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'space-between', gap: theme.spacing.m, marginBottom: theme.spacing.xl },
  wordBox: { width: '47%', backgroundColor: theme.colors.backgroundTertiary, padding: theme.spacing.m, borderRadius: theme.borderRadius.m, flexDirection: 'row', alignItems: 'center' },
  wordNumber: { width: 24 },
  copyButton: { marginBottom: theme.spacing.m },
});
import React, { useState } from 'react';
import { View, StyleSheet, TouchableOpacity, Switch, Alert, ActivityIndicator } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { SafeAreaViewWrapper } from '@/components/layout/SafeAreaViewWrapper';
import { Header } from '@/components/layout/Header';
import { Container } from '@/components/layout/Container';
import { Typography } from '@/components/common/Typography';
import { Icon, IconName } from '@/components/common/Icon';
import { Button } from '@/components/common/Button';
import { theme } from '@/styles/theme';
import { useAuth } from '@/hooks/useAuth';
import { maskString } from '@/utils/helpers';

interface SettingsOptionProps {
  title: string;
  subtitle?: string;
  icon: IconName;
  onPress?: () => void;
  isSwitch?: boolean;
  switchValue?: boolean;
  onSwitchChange?: (val: boolean) => void;
  danger?: boolean;
}

const SettingsOption: React.FC<SettingsOptionProps> = ({ 
  title, subtitle, icon, onPress, isSwitch, switchValue, onSwitchChange, danger 
}) => (
  <TouchableOpacity 
    style={styles.optionContainer} 
    onPress={onPress} 
    disabled={isSwitch || !onPress}
    activeOpacity={0.7}
  >
    <View style={styles.optionLeft}>
      <View style={[styles.iconWrapper, danger && { backgroundColor: 'rgba(255, 77, 77, 0.1)' }]}>
        <Icon name={icon} size={20} color={danger ? theme.colors.error : theme.colors.primary} />
      </View>
      <View>
        <Typography variant="body" weight="medium" color={danger ? theme.colors.error : theme.colors.textPrimary}>
          {title}
        </Typography>
        {/* FIX: Changed subtitle && to subtitle ? : null */}
        {subtitle ? (
          <Typography variant="caption" color={theme.colors.textSecondary}>
            {subtitle}
          </Typography>
        ) : null}
      </View>
    </View>
    
    {isSwitch ? (
      <Switch
        value={switchValue}
        onValueChange={onSwitchChange}
        trackColor={{ false: theme.colors.border, true: theme.colors.primary }}
        thumbColor="#FFF"
      />
    ) : (
      <Icon name="chevron-right" size={20} color={theme.colors.textSecondary} />
    )}
  </TouchableOpacity>
);

export default function SettingsScreen() {
  const navigation = useNavigation<any>();
  const { user, logout } = useAuth();
  const [loggingOut, setLoggingOut] = useState(false);
  const [hideBalances, setHideBalances] = useState(false); // Can be tied to a context later

  const handleLogout = async () => {
    Alert.alert('Log Out', 'Are you sure you want to log out of your wallet?', [
      { text: 'Cancel', style: 'cancel' },
      { 
        text: 'Log Out', 
        style: 'destructive',
        onPress: async () => {
          setLoggingOut(true);
          await logout();
        }
      }
    ]);
  };

  if (loggingOut) {
    return (
      <SafeAreaViewWrapper centered>
        <ActivityIndicator size="large" color={theme.colors.primary} />
        <Typography variant="body" style={{ marginTop: theme.spacing.m }}>Logging out safely...</Typography>
      </SafeAreaViewWrapper>
    );
  }

  return (
    <SafeAreaViewWrapper>
      <Header title="Settings" showBack={false} />
      <Container scrollable contentContainerStyle={styles.container}>
        
        {/* Profile Card */}
        <View style={styles.profileCard}>
          <View style={styles.avatar}>
            <Typography variant="h2" color="#FFF" weight="bold">
              {user?.username?.charAt(0).toUpperCase() || 'U'}
            </Typography>
          </View>
          <View style={styles.profileInfo}>
            <Typography variant="h3" weight="bold">{user?.username || 'User'}</Typography>
            <Typography variant="caption" color={theme.colors.textSecondary}>
              {maskString(user?.email || '', 3, 5)}
            </Typography>
          </View>
          <View style={styles.kycBadge}>
            <Typography variant="caption" color={theme.colors.primary} weight="bold">
              Tier {user?.kyc_level || 0}
            </Typography>
          </View>
        </View>

        <Typography variant="label" color={theme.colors.textSecondary} style={styles.sectionTitle}>
          PREFERENCES
        </Typography>
        <View style={styles.section}>
          <SettingsOption 
            title="Hide Balances" 
            subtitle="Mask balances across the app" 
            icon="eye-off" 
            isSwitch 
            switchValue={hideBalances}
            onSwitchChange={setHideBalances}
          />
          <SettingsOption title="Currency" subtitle="USD ($)" icon="dollar-sign" onPress={() => {}} />
          <SettingsOption title="Appearance" subtitle="Dark Mode" icon="moon" onPress={() => {}} />
        </View>

        <Typography variant="label" color={theme.colors.textSecondary} style={styles.sectionTitle}>
          SECURITY & COMPLIANCE
        </Typography>
        <View style={styles.section}>
          <SettingsOption title="Security Center" subtitle="PIN, Biometrics, 2FA" icon="shield" onPress={() => navigation.navigate('Security')} />
          <SettingsOption title="Verification (KYC)" subtitle="Upgrade your limits" icon="check-circle" onPress={() => navigation.navigate('KYC')} />
          <SettingsOption title="Manage Wallets" subtitle="View seeds & private keys" icon="key" onPress={() => {}} />
        </View>

        <Typography variant="label" color={theme.colors.textSecondary} style={styles.sectionTitle}>
          ABOUT
        </Typography>
        <View style={styles.section}>
          <SettingsOption title="Support" icon="help-circle" onPress={() => {}} />
          <SettingsOption title="Terms of Service" icon="file-text" onPress={() => {}} />
        </View>

        <Button 
          title="Log Out" 
          variant="danger" 
          icon="log-out"
          onPress={handleLogout} 
          style={styles.logoutButton}
        />
        
        <Typography variant="caption" color={theme.colors.textTertiary} align="center" style={styles.version}>
          Ruvox v1.0.0
        </Typography>
      </Container>
    </SafeAreaViewWrapper>
  );
}

const styles = StyleSheet.create({
  container: { paddingBottom: theme.spacing.xxl },
  profileCard: { flexDirection: 'row', alignItems: 'center', backgroundColor: theme.colors.backgroundSecondary, padding: theme.spacing.m, borderRadius: theme.borderRadius.l, marginTop: theme.spacing.m, marginBottom: theme.spacing.xl },
  avatar: { width: 48, height: 48, borderRadius: 24, backgroundColor: theme.colors.primary, alignItems: 'center', justifyContent: 'center' },
  profileInfo: { flex: 1, marginLeft: theme.spacing.m },
  kycBadge: { backgroundColor: 'rgba(153, 69, 255, 0.1)', paddingHorizontal: 12, paddingVertical: 4, borderRadius: 12, borderWidth: 1, borderColor: 'rgba(153, 69, 255, 0.3)' },
  sectionTitle: { marginLeft: theme.spacing.s, marginBottom: theme.spacing.s },
  section: { backgroundColor: theme.colors.backgroundSecondary, borderRadius: theme.borderRadius.l, marginBottom: theme.spacing.xl, overflow: 'hidden' },
  optionContainer: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', padding: theme.spacing.m, borderBottomWidth: 1, borderBottomColor: theme.colors.divider },
  optionLeft: { flexDirection: 'row', alignItems: 'center' },
  iconWrapper: { width: 36, height: 36, borderRadius: 18, backgroundColor: theme.colors.backgroundTertiary, alignItems: 'center', justifyContent: 'center', marginRight: theme.spacing.m },
  logoutButton: { marginVertical: theme.spacing.l },
  version: { marginBottom: theme.spacing.xxl },
});
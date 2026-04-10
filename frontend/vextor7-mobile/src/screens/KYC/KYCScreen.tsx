import React, { useState } from 'react';
import { View, StyleSheet, Image, KeyboardAvoidingView, Platform, Alert, TouchableOpacity } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import * as ImagePicker from 'expo-image-picker';
import { SafeAreaViewWrapper } from '@/components/layout/SafeAreaViewWrapper';
import { Header } from '@/components/layout/Header';
import { Container } from '@/components/layout/Container';
import { Typography } from '@/components/common/Typography';
import { Button } from '@/components/common/Button';
import { Input } from '@/components/common/Input';
import { Icon } from '@/components/common/Icon';
import { theme } from '@/styles/theme';
import { useKycStatus } from '@/hooks/useKycStatus';
import { securityApi } from '@/api/services/securityApi';

export default function KYCScreen() {
  const navigation = useNavigation();
  const { level, status, loading, refresh } = useKycStatus();
  
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  // Tier 1 Form
  const [fullName, setFullName] = useState('');
  const [dob, setDob] = useState('');
  const [address, setAddress] = useState('');

  // Tier 2 Form
  const [frontImage, setFrontImage] = useState<string | null>(null);
  const [backImage, setBackImage] = useState<string | null>(null);

  const pickImage = async (side: 'front' | 'back') => {
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsEditing: true,
      quality: 0.8,
    });

    if (!result.canceled) {
      if (side === 'front') setFrontImage(result.assets[0].uri);
      else setBackImage(result.assets[0].uri);
    }
  };

  const handleSubmitTier1 = async () => {
    if (!fullName || !dob || !address) {
      Alert.alert('Error', 'Please fill in all fields.');
      return;
    }

    try {
      setIsSubmitting(true);
      const formData = new FormData();
      formData.append('level', '1');
      formData.append('full_name', fullName);
      formData.append('dob', dob);
      formData.append('address', address);

      await securityApi.submitKyc(formData);
      Alert.alert('Success', 'Tier 1 details submitted.');
      await refresh();
    } catch (error) {
      Alert.alert('Error', 'Submission failed.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSubmitTier2 = async () => {
    if (!frontImage || !backImage) {
      Alert.alert('Error', 'Please upload both front and back of your ID.');
      return;
    }

    try {
      setIsSubmitting(true);
      const formData = new FormData();
      formData.append('level', '2');
      
      // Format image for React Native FormData
      formData.append('document_front', {
        uri: frontImage,
        name: 'front.jpg',
        type: 'image/jpeg',
      } as any);

      formData.append('document_back', {
        uri: backImage,
        name: 'back.jpg',
        type: 'image/jpeg',
      } as any);

      await securityApi.submitKyc(formData);
      Alert.alert('Success', 'Documents submitted for review.');
      await refresh();
    } catch (error) {
      Alert.alert('Error', 'Upload failed.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const renderStatusBadge = () => {
    if (status === 'PENDING') return <View style={[styles.badge, styles.badgePending]}><Typography variant="caption" color="#FFD700">Under Review</Typography></View>;
    if (status === 'REJECTED') return <View style={[styles.badge, styles.badgeError]}><Typography variant="caption" color="#FF4D4D">Rejected</Typography></View>;
    return <View style={[styles.badge, styles.badgeSuccess]}><Typography variant="caption" color="#14F195">Verified</Typography></View>;
  };

  return (
    <SafeAreaViewWrapper>
      <Header title="Verification" />
      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : 'height'} style={{ flex: 1 }}>
        <Container scrollable contentContainerStyle={styles.container}>
          
          {/* Current Status Card */}
          <View style={styles.statusCard}>
            <View style={styles.statusHeader}>
              <View>
                <Typography variant="body" color={theme.colors.textSecondary}>Current Tier</Typography>
                <Typography variant="h1" weight="bold">Tier {level}</Typography>
              </View>
              {renderStatusBadge()}
            </View>
            <View style={styles.divider} />
            <Typography variant="caption" color={theme.colors.textSecondary}>
              Daily Withdrawal Limit: {level === 0 ? '$0' : level === 1 ? '$1,000' : '$10,000'}
            </Typography>
          </View>

          {status === 'PENDING' && (
            <View style={styles.pendingContainer}>
              <Icon name="clock" size={48} color={theme.colors.warning} />
              <Typography variant="h3" weight="bold" style={{ marginTop: theme.spacing.m }}>Review in Progress</Typography>
              <Typography variant="body" color={theme.colors.textSecondary} align="center" style={{ marginTop: theme.spacing.s }}>
                Your submission is being verified. This usually takes 5-10 minutes.
              </Typography>
            </View>
          )}

          {/* Form for Tier 1 */}
          {level === 0 && status !== 'PENDING' && (
            <View style={styles.formContainer}>
              <Typography variant="h3" weight="bold" style={{ marginBottom: theme.spacing.m }}>Upgrade to Tier 1</Typography>
              <Input label="Full Legal Name" placeholder="John Doe" value={fullName} onChangeText={setFullName} />
              <Input label="Date of Birth" placeholder="YYYY-MM-DD" value={dob} onChangeText={setDob} />
              <Input label="Residential Address" placeholder="123 Main St..." value={address} onChangeText={setAddress} />
              <Button title="Submit Details" onPress={handleSubmitTier1} loading={isSubmitting} style={{ marginTop: theme.spacing.l }} />
            </View>
          )}

          {/* Form for Tier 2 */}
          {level === 1 && status !== 'PENDING' && (
            <View style={styles.formContainer}>
              <Typography variant="h3" weight="bold" style={{ marginBottom: theme.spacing.s }}>Upgrade to Tier 2</Typography>
              <Typography variant="caption" color={theme.colors.textSecondary} style={{ marginBottom: theme.spacing.l }}>
                Upload a valid government-issued ID (Passport, Driver's License)
              </Typography>

              <View style={styles.uploadRow}>
                <TouchableOpacity style={styles.uploadBox} onPress={() => pickImage('front')}>
                  {frontImage ? (
                    <Image source={{ uri: frontImage }} style={styles.imagePreview} />
                  ) : (
                    <>
                      <Icon name="camera" size={24} color={theme.colors.primary} />
                      <Typography variant="caption" style={{ marginTop: 8 }}>Front of ID</Typography>
                    </>
                  )}
                </TouchableOpacity>

                <TouchableOpacity style={styles.uploadBox} onPress={() => pickImage('back')}>
                  {backImage ? (
                    <Image source={{ uri: backImage }} style={styles.imagePreview} />
                  ) : (
                    <>
                      <Icon name="camera" size={24} color={theme.colors.primary} />
                      <Typography variant="caption" style={{ marginTop: 8 }}>Back of ID</Typography>
                    </>
                  )}
                </TouchableOpacity>
              </View>

              <Button 
                title="Upload Documents" 
                onPress={handleSubmitTier2} 
                loading={isSubmitting} 
                disabled={!frontImage || !backImage}
                style={{ marginTop: theme.spacing.xl }} 
              />
            </View>
          )}

        </Container>
      </KeyboardAvoidingView>
    </SafeAreaViewWrapper>
  );
}

const styles = StyleSheet.create({
  container: { paddingTop: theme.spacing.m, paddingBottom: theme.spacing.xxl },
  statusCard: { backgroundColor: theme.colors.backgroundSecondary, padding: theme.spacing.l, borderRadius: theme.borderRadius.l, marginBottom: theme.spacing.xl },
  statusHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  badge: { paddingHorizontal: 12, paddingVertical: 4, borderRadius: 12, borderWidth: 1 },
  badgeSuccess: { backgroundColor: 'rgba(20, 241, 149, 0.1)', borderColor: 'rgba(20, 241, 149, 0.3)' },
  badgePending: { backgroundColor: 'rgba(255, 215, 0, 0.1)', borderColor: 'rgba(255, 215, 0, 0.3)' },
  badgeError: { backgroundColor: 'rgba(255, 77, 77, 0.1)', borderColor: 'rgba(255, 77, 77, 0.3)' },
  divider: { height: 1, backgroundColor: theme.colors.divider, marginVertical: theme.spacing.m },
  formContainer: { backgroundColor: theme.colors.backgroundSecondary, padding: theme.spacing.l, borderRadius: theme.borderRadius.l },
  pendingContainer: { alignItems: 'center', justifyContent: 'center', paddingVertical: theme.spacing.xxl },
  uploadRow: { flexDirection: 'row', justifyContent: 'space-between', gap: theme.spacing.m },
  uploadBox: { flex: 1, height: 120, borderRadius: theme.borderRadius.m, borderWidth: 2, borderColor: theme.colors.divider, borderStyle: 'dashed', alignItems: 'center', justifyContent: 'center', overflow: 'hidden' },
  imagePreview: { width: '100%', height: '100%', resizeMode: 'cover' },
});
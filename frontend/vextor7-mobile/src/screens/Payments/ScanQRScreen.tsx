import React, { useState, useEffect } from 'react';
import { View, StyleSheet, TouchableOpacity } from 'react-native';
import { Camera, CameraView } from 'expo-camera';
import { useNavigation } from '@react-navigation/native';
import { SafeAreaViewWrapper } from '@/components/layout/SafeAreaViewWrapper';
import { Typography } from '@/components/common/Typography';
import { Icon } from '@/components/common/Icon';
import { Button } from '@/components/common/Button';
import { theme } from '@/styles/theme';
import { parsePaymentUri } from '@/utils/blockchain';

export default function ScanQRScreen() {
  const navigation = useNavigation<any>();
  const [hasPermission, setHasPermission] = useState<boolean | null>(null);
  const [scanned, setScanned] = useState(false);

  useEffect(() => {
    const getCameraPermissions = async () => {
      const { status } = await Camera.requestCameraPermissionsAsync();
      setHasPermission(status === 'granted');
    };
    getCameraPermissions();
  }, []);

  const handleBarCodeScanned = ({ data }: { data: string }) => {
    setScanned(true);
    const parsed = parsePaymentUri(data);
    
    if (parsed) {
      // Navigate to Send screen pre-filled
      navigation.navigate('WalletTab', {
        screen: 'Send',
        params: { toAddress: parsed.address, amount: parsed.amount } // Need to align with Send route params
      });
    } else {
      alert('Invalid QR Code');
      setTimeout(() => setScanned(false), 2000);
    }
  };

  if (hasPermission === null) return <SafeAreaViewWrapper><View /></SafeAreaViewWrapper>;
  if (hasPermission === false) return (
    <SafeAreaViewWrapper centered>
      <Typography>No access to camera</Typography>
      <Button title="Go Back" onPress={() => navigation.goBack()} style={{ marginTop: 20 }} />
    </SafeAreaViewWrapper>
  );

  return (
    <View style={styles.container}>
      <CameraView
        style={StyleSheet.absoluteFillObject}
        onBarcodeScanned={scanned ? undefined : handleBarCodeScanned}
        barcodeScannerSettings={{
          barcodeTypes: ["qr"],
        }}
      />
      <SafeAreaViewWrapper transparent isRoot>
        <View style={styles.header}>
          <TouchableOpacity onPress={() => navigation.goBack()} style={styles.closeBtn}>
            <Icon name="x" size={24} color="#FFF" />
          </TouchableOpacity>
          <Typography variant="h3" weight="bold" color="#FFF">Scan to Pay</Typography>
          <View style={{ width: 40 }} />
        </View>

        <View style={styles.overlay}>
          <View style={styles.scanBox} />
          <Typography variant="body" color="#FFF" style={styles.scanText}>
            Align QR code within the frame
          </Typography>
        </View>
      </SafeAreaViewWrapper>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#000' },
  header: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingHorizontal: theme.spacing.m, height: 60, zIndex: 10 },
  closeBtn: { padding: 8, backgroundColor: 'rgba(0,0,0,0.5)', borderRadius: 20 },
  overlay: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  scanBox: { width: 250, height: 250, borderWidth: 2, borderColor: theme.colors.primary, backgroundColor: 'transparent', borderRadius: theme.borderRadius.l },
  scanText: { marginTop: theme.spacing.xl, backgroundColor: 'rgba(0,0,0,0.6)', paddingHorizontal: 16, paddingVertical: 8, borderRadius: 20 },
});
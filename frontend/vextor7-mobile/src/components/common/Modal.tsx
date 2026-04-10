import React from 'react';
import { 
  Modal as RNModal, 
  View, 
  StyleSheet, 
  TouchableOpacity, 
  KeyboardAvoidingView, 
  Platform 
} from 'react-native';
import { theme } from '@/styles/theme';
import { Typography } from './Typography';
import { Icon } from './Icon';
import { BlurView } from 'expo-blur'; // Assuming expo-blur is standard for glass effect

interface ModalProps {
  visible: boolean;
  onClose: () => void;
  title?: string;
  children: React.ReactNode;
  height?: number | string;
}

export const Modal: React.FC<ModalProps> = ({
  visible,
  onClose,
  title,
  children,
  height = 'auto',
}) => {
  return (
    <RNModal
      visible={visible}
      transparent
      animationType="slide"
      onRequestClose={onClose}
      statusBarTranslucent
    >
      <View style={styles.overlay}>
        {/* Backdrop Tap to Close */}
        <TouchableOpacity 
          style={StyleSheet.absoluteFill} 
          onPress={onClose} 
          activeOpacity={1} 
        />
        
        <KeyboardAvoidingView
          behavior={Platform.OS === 'ios' ? 'padding' : undefined}
          style={styles.keyboardAvoid}
        >
          <View style={[styles.container, { height: typeof height === 'number' ? height : undefined }]}>
            <View style={styles.handle} />
            
            <View style={styles.header}>
              <Typography variant="h3" weight="bold">
                {title || ' '}
              </Typography>
              <TouchableOpacity onPress={onClose} style={styles.closeBtn}>
                <Icon name="x" size={24} color={theme.colors.textSecondary} />
              </TouchableOpacity>
            </View>

            <View style={styles.content}>
              {children}
            </View>
          </View>
        </KeyboardAvoidingView>
      </View>
    </RNModal>
  );
};

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.6)',
    justifyContent: 'flex-end',
  },
  keyboardAvoid: {
    width: '100%',
  },
  container: {
    backgroundColor: theme.colors.backgroundSecondary,
    borderTopLeftRadius: theme.borderRadius.xl,
    borderTopRightRadius: theme.borderRadius.xl,
    paddingBottom: theme.spacing.xxl, // Safe area for bottom
    width: '100%',
    maxHeight: '90%',
  },
  handle: {
    width: 40,
    height: 4,
    backgroundColor: theme.colors.border,
    borderRadius: 2,
    alignSelf: 'center',
    marginTop: theme.spacing.s,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: theme.spacing.l,
    paddingTop: theme.spacing.m,
    paddingBottom: theme.spacing.m,
    borderBottomWidth: 1,
    borderBottomColor: theme.colors.border,
  },
  closeBtn: {
    padding: 4,
  },
  content: {
    padding: theme.spacing.l,
  },
});
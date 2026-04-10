import React, { useState } from 'react';
import { View, TextInput, StyleSheet, TouchableOpacity, TextInputProps } from 'react-native';
import { theme } from '@/styles/theme';
import { Typography } from './Typography';
import { Icon, IconName } from './Icon';

interface InputProps extends TextInputProps {
  label?: string;
  error?: string;
  leftIcon?: IconName;
  rightIcon?: IconName;
  onRightIconPress?: () => void;
  secureTextEntry?: boolean;
}

export const Input: React.FC<InputProps> = ({
  label,
  error,
  leftIcon,
  rightIcon,
  onRightIconPress,
  secureTextEntry,
  style,
  ...props
}) => {
  const [isFocused, setIsFocused] = useState(false);
  const [isPasswordVisible, setIsPasswordVisible] = useState(!secureTextEntry);

  const togglePasswordVisibility = () => setIsPasswordVisible(!isPasswordVisible);

  const borderColor = error
    ? theme.colors.error
    : isFocused
    ? theme.colors.primary
    : theme.colors.border;

  return (
    <View style={styles.container}>
      {label ? (
        <Typography variant="label" color={theme.colors.textSecondary} style={styles.label}>
          {label}
        </Typography>
      ) : null}
      
      <View style={[styles.inputContainer, { borderColor }]}>
        {leftIcon ? (
          <Icon name={leftIcon} size={20} color={theme.colors.textSecondary} style={styles.leftIcon} />
        ) : null}
        
        <TextInput
          style={[styles.input, { color: theme.colors.textPrimary }, leftIcon ? { paddingLeft: 0 } : {}]}
          placeholderTextColor={theme.colors.textTertiary}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          secureTextEntry={secureTextEntry && !isPasswordVisible}
          {...props}
        />

        {secureTextEntry ? (
          <TouchableOpacity onPress={togglePasswordVisibility} style={styles.rightIcon}>
            <Icon name={isPasswordVisible ? 'eye-off' : 'eye'} size={20} color={theme.colors.textSecondary} />
          </TouchableOpacity>
        ) : rightIcon ? (
          <TouchableOpacity onPress={onRightIconPress} style={styles.rightIcon}>
            <Icon name={rightIcon} size={20} color={theme.colors.textSecondary} />
          </TouchableOpacity>
        ) : null}
      </View>

      {error ? (
        <Typography variant="caption" color={theme.colors.error} style={styles.error}>
          {error}
        </Typography>
      ) : null}
    </View>
  );
};

const styles = StyleSheet.create({
  container: { marginBottom: theme.spacing.m, width: '100%' },
  label: { marginBottom: theme.spacing.xs },
  inputContainer: { flexDirection: 'row', alignItems: 'center', height: theme.components.input.height, backgroundColor: theme.components.input.backgroundColor, borderRadius: theme.components.input.borderRadius, borderWidth: 1, paddingHorizontal: theme.spacing.m },
  input: { flex: 1, height: '100%', fontSize: theme.typography.m },
  leftIcon: { marginRight: theme.spacing.s },
  rightIcon: { marginLeft: theme.spacing.s, padding: 4 },
  error: { marginTop: theme.spacing.xs },
});
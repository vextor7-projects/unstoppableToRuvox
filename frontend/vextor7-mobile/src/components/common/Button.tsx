import React from 'react';
import { TouchableOpacity, ActivityIndicator, StyleSheet, ViewStyle, TextStyle } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Typography } from './Typography';
import { theme } from '@/styles/theme';
import { Icon, IconName, IconSet } from './Icon';

interface ButtonProps {
  title: string;
  onPress: () => void;
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger';
  loading?: boolean;
  disabled?: boolean;
  icon?: IconName;
  iconSet?: IconSet;
  fullWidth?: boolean;
  style?: ViewStyle;
}

export const Button: React.FC<ButtonProps> = ({
  title,
  onPress,
  variant = 'primary',
  loading = false,
  disabled = false,
  icon,
  iconSet,
  fullWidth = true,
  style,
}) => {
  const isPrimary = variant === 'primary';
  const isDanger = variant === 'danger';
  
  const containerStyle: ViewStyle = {
    height: theme.components.button.height,
    borderRadius: theme.components.button.borderRadius,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    width: fullWidth ? '100%' : 'auto',
    paddingHorizontal: fullWidth ? 0 : theme.spacing.l,
    opacity: disabled ? 0.6 : 1,
    backgroundColor: variant === 'secondary' ? theme.colors.backgroundTertiary : 
                     variant === 'danger' ? 'rgba(255, 77, 77, 0.1)' : 'transparent',
    borderWidth: variant === 'outline' ? 1 : 0,
    borderColor: variant === 'outline' ? theme.colors.border : 'transparent',
  };

  const textColor = isPrimary ? theme.colors.textInverse : 
                    isDanger ? theme.colors.error : 
                    theme.colors.textPrimary;

  const content = (
    <>
      {loading ? (
        <ActivityIndicator color={textColor} />
      ) : (
        <>
          {icon && (
            <Icon 
              name={icon} 
              set={iconSet} 
              size={20} 
              color={textColor} 
              style={{ marginRight: theme.spacing.s }} 
            />
          )}
          <Typography variant="button" color={textColor}>
            {title}
          </Typography>
        </>
      )}
    </>
  );

  if (isPrimary && !disabled && !loading) {
    return (
      <TouchableOpacity 
        onPress={onPress} 
        disabled={disabled || loading} 
        activeOpacity={0.8}
        style={[style, { width: fullWidth ? '100%' : 'auto' }]}
      >
        <LinearGradient
          colors={theme.colors.gradients.primary}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 0 }}
          style={[containerStyle, { backgroundColor: 'transparent' }]}
        >
          {content}
        </LinearGradient>
      </TouchableOpacity>
    );
  }

  return (
    <TouchableOpacity
      onPress={onPress}
      disabled={disabled || loading}
      activeOpacity={0.7}
      style={[containerStyle, style]}
    >
      {content}
    </TouchableOpacity>
  );
};
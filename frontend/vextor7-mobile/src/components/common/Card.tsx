import React from 'react';
import { View, StyleSheet, ViewStyle, TouchableOpacity } from 'react-native';
import { theme } from '@/styles/theme';

interface CardProps {
  children: React.ReactNode;
  variant?: 'default' | 'elevated' | 'outlined' | 'flat';
  onPress?: () => void;
  style?: ViewStyle;
  padding?: keyof typeof theme.spacing;
}

export const Card: React.FC<CardProps> = ({
  children,
  variant = 'default',
  onPress,
  style,
  padding = 'm',
}) => {
  const containerStyle: ViewStyle = {
    backgroundColor: variant === 'outlined' ? 'transparent' : theme.colors.backgroundSecondary,
    borderRadius: theme.components.card.borderRadius,
    padding: theme.spacing[padding],
    borderWidth: variant === 'outlined' ? 1 : 0,
    borderColor: theme.colors.border,
    // Add shadow only if elevated and not simple dark mode flat look (optional in deep dark UI)
  };

  if (onPress) {
    return (
      <TouchableOpacity 
        onPress={onPress} 
        activeOpacity={0.7} 
        style={[containerStyle, style]}
      >
        {children}
      </TouchableOpacity>
    );
  }

  return <View style={[containerStyle, style]}>{children}</View>;
};
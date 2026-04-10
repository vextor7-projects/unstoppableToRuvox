import React from 'react';
import { Text, TextProps, TextStyle, StyleSheet } from 'react-native';
import { theme } from '@/styles/theme';

interface TypographyProps extends TextProps {
  variant?: 'h1' | 'h2' | 'h3' | 'body' | 'caption' | 'label' | 'button' | 'price'| 'xxxl';
  color?: string;
  align?: 'left' | 'center' | 'right';
  weight?: 'regular' | 'medium' | 'bold';
  children: React.ReactNode;
}

export const Typography: React.FC<TypographyProps> = ({
  variant = 'body',
  color = theme.colors.textPrimary,
  align = 'left',
  weight = 'regular',
  style,
  children,
  ...props
}) => {
  const getFontSize = () => {
    switch (variant) {
      case 'xxxl': return theme.typography.xxxl;
      case 'h1': return theme.typography.xxxl;
      case 'h2': return theme.typography.xl;
      case 'h3': return theme.typography.l;
      case 'price': return theme.typography.xxl;
      case 'button': return theme.typography.m;
      case 'caption': return theme.typography.xs;
      case 'label': return theme.typography.s;
      default: return theme.typography.m;
    }
  };

  const getFontWeight = (): TextStyle['fontWeight'] => {
    if (weight === 'bold') return '700';
    if (weight === 'medium') return '500';
    if (variant === 'h1' || variant === 'h2' || variant === 'price') return '700';
    if (variant === 'button') return '600';
    return '400';
  };

  const textStyles: TextStyle = {
    fontSize: getFontSize(),
    fontWeight: getFontWeight(),
    color: color,
    textAlign: align,
  };

  return (
    <Text style={[textStyles, style]} {...props}>
      {children}
    </Text>
  );
};
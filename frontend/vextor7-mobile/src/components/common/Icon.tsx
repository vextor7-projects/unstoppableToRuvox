import React from 'react';
import { Feather, MaterialIcons, Ionicons } from '@expo/vector-icons';
import { useTheme } from '@react-navigation/native'; // Or custom theme hook
import { theme } from '@/styles/theme';

export type IconSet = 'Feather' | 'Material' | 'Ionicons';
export type IconName = keyof typeof Feather.glyphMap | keyof typeof MaterialIcons.glyphMap | keyof typeof Ionicons.glyphMap;

interface IconProps {
  name: any; // Type looseness to allow different sets, strict typing requires complex conditionals
  set?: IconSet;
  size?: number;
  color?: string;
  style?: any;
}

export const Icon: React.FC<IconProps> = ({ 
  name, 
  set = 'Feather', 
  size = 24, 
  color = theme.colors.textPrimary,
  style 
}) => {
  switch (set) {
    case 'Material':
      return <MaterialIcons name={name} size={size} color={color} style={style} />;
    case 'Ionicons':
      return <Ionicons name={name} size={size} color={color} style={style} />;
    default:
      return <Feather name={name} size={size} color={color} style={style} />;
  }
};
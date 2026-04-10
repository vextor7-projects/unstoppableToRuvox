// src/constants/dimensions.ts
import { Dimensions, Platform } from 'react-native';

const { width, height } = Dimensions.get('window');

export const DIMENSIONS = {
  // Screen
  windowWidth: width,
  windowHeight: height,
  isSmallDevice: width < 375,

  // Spacing (8pt grid system)
  spacing: {
    xs: 4,
    s: 8,
    m: 16,
    l: 24,
    xl: 32,
    xxl: 40,
  },

  // Layout
  borderRadius: {
    s: 8,
    m: 12, // Standard for inputs/buttons
    l: 16, // Standard for cards
    xl: 24,
    round: 9999, // For circular buttons
  },

  // Typography (Pixel perfect sizes)
  fontSize: {
    xs: 12,
    s: 14,
    m: 16, // Body text
    l: 18,
    xl: 24, // Headers
    xxl: 32, // Large Balances
    xxxl: 40,
  },

  iconSize: {
    s: 16,
    m: 24, // Standard icon size
    l: 32,
    xl: 48,
  },
  
  // UI Specific
  buttonHeight: 56,
  inputHeight: 56,
  bottomTabHeight: Platform.OS === 'ios' ? 88 : 60,
  headerHeight: Platform.OS === 'ios' ? 44 : 56,
} as const;
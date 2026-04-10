// src/constants/colors.ts

export const COLORS = {
  // Core Backgrounds
  background: '#000000', // Deep black as seen in designs
  backgroundSecondary: '#121212', // Slightly lighter for cards/modals
  backgroundTertiary: '#1E1E1E', // Input fields, secondary cards

  // Typography
  textPrimary: '#FFFFFF',
  textSecondary: '#A0A0A0', // Muted text for labels
  textTertiary: '#666666', // Placeholders
  textInverse: '#000000',

  // Branding & Gradients (Solana/Ruvox Theme)
  primary: '#9945FF', // Solana Purple
  secondary: '#14F195', // Solana Green
  accent: '#00C2FF', // Cyan/Blue
  
  // Gradient Stops (for LinearGradient components)
  gradients: {
    primary: ['#9945FF', '#14F195'], // Purple to Green
    secondary: ['#00C2FF', '#0047FF'], // Cyan to Blue
    card: ['#1A1A1A', '#000000'], // Subtle card gradient
    darkOverlay: ['transparent', 'rgba(0,0,0,0.9)'],
  },

  // Functional Colors
  success: '#14F195', // Green for positive change/success
  warning: '#FFD700', // Yellow for pending/warning
  error: '#FF4D4D', // Red for errors/negative change
  info: '#00C2FF',
  
  // UI Elements
  border: '#333333',
  divider: '#2A2A2A',
  overlay: 'rgba(0, 0, 0, 0.7)',
  skeleton: '#2C2C2C',
} as const;
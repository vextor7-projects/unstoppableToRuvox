import { COLORS } from '@/constants/colors';
import { DIMENSIONS } from '@/constants/dimensions';

export interface ThemeType {
  colors: typeof COLORS;
  spacing: typeof DIMENSIONS.spacing;
  borderRadius: typeof DIMENSIONS.borderRadius;
  typography: typeof DIMENSIONS.fontSize;
  layout: {
    windowWidth: number;
    windowHeight: number;
    isSmallDevice: boolean;
    headerHeight: number;
    bottomTabHeight: number;
  };
  components: {
    button: {
      height: number;
      borderRadius: number;
    };
    input: {
      height: number;
      borderRadius: number;
      backgroundColor: string;
      placeholderColor: string;
    };
    card: {
      backgroundColor: string;
      borderRadius: number;
      padding: number;
    };
  };
}

export const theme: ThemeType = {
  colors: COLORS,
  spacing: DIMENSIONS.spacing,
  borderRadius: DIMENSIONS.borderRadius,
  typography: DIMENSIONS.fontSize,
  layout: {
    windowWidth: DIMENSIONS.windowWidth,
    windowHeight: DIMENSIONS.windowHeight,
    isSmallDevice: DIMENSIONS.isSmallDevice,
    headerHeight: DIMENSIONS.headerHeight,
    bottomTabHeight: DIMENSIONS.bottomTabHeight,
  },
  components: {
    button: {
      height: DIMENSIONS.buttonHeight,
      borderRadius: DIMENSIONS.borderRadius.m,
    },
    input: {
      height: DIMENSIONS.inputHeight,
      borderRadius: DIMENSIONS.borderRadius.m,
      backgroundColor: COLORS.backgroundTertiary,
      placeholderColor: COLORS.textTertiary,
    },
    card: {
      backgroundColor: COLORS.backgroundSecondary,
      borderRadius: DIMENSIONS.borderRadius.l,
      padding: DIMENSIONS.spacing.m,
    },
  },
};

// If we need a light theme in the future, we would define `lightTheme` here overriding specific colors.
// For now, Ruvox is strictly Dark Mode as per design requirements.
export default theme;
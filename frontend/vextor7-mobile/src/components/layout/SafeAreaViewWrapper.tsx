import React from 'react';
import { ViewStyle, StatusBar } from 'react-native';
import { SafeAreaView, SafeAreaViewProps } from 'react-native-safe-area-context';
import { theme } from '@/styles/theme';

interface WrapperProps extends SafeAreaViewProps {
  children: React.ReactNode;
  backgroundColor?: string;
  isRoot?: boolean; 
  centered?: boolean;
  transparent?: boolean;
}

export const SafeAreaViewWrapper: React.FC<WrapperProps> = ({
  children,
  backgroundColor = theme.colors.background,
  style,
  isRoot = false,
  centered = false,
  transparent = false,
  ...props
}) => {
  
  const finalBgColor = transparent ? 'transparent' : backgroundColor;

  return (
    <SafeAreaView 
      style={[
        { flex: 1, backgroundColor: finalBgColor }, 
        centered && { justifyContent: 'center', alignItems: 'center' },
        style
      ]} 
      {...props}
    >
      {isRoot && (
        <StatusBar 
          barStyle="light-content" 
          backgroundColor={transparent ? 'transparent' : finalBgColor} 
          translucent={transparent} 
        />
      )}
      {children}
    </SafeAreaView>
  );
};
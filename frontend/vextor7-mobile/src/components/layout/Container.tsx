import React from 'react';
import { View, ScrollView, StyleSheet, ViewStyle, RefreshControl } from 'react-native';
import { theme } from '@/styles/theme';

interface ContainerProps {
  children: React.ReactNode;
  scrollable?: boolean;
  centered?: boolean;
  style?: ViewStyle;
  contentContainerStyle?: ViewStyle;
  onRefresh?: () => void;
  refreshing?: boolean;
}

export const Container: React.FC<ContainerProps> = ({
  children,
  scrollable = false,
  centered = false,
  style,
  contentContainerStyle,
  onRefresh,
  refreshing = false,
}) => {
  const baseStyle: ViewStyle = {
    flex: 1,
    paddingHorizontal: theme.spacing.l,
    backgroundColor: theme.colors.background,
    justifyContent: centered ? 'center' : 'flex-start',
  };

  if (scrollable) {
    return (
      <ScrollView
        style={[styles.scroll, style]}
        contentContainerStyle={[
          baseStyle, 
          styles.scrollContent, 
          centered && { flexGrow: 1 },
          contentContainerStyle
        ]}
        showsVerticalScrollIndicator={false}
        keyboardShouldPersistTaps="handled"
        refreshControl={
          onRefresh ? (
            <RefreshControl 
              refreshing={refreshing} 
              onRefresh={onRefresh} 
              tintColor={theme.colors.primary} // iOS spinner color
              colors={[theme.colors.primary]} // Android spinner colors
              progressBackgroundColor={theme.colors.backgroundSecondary}
            />
          ) : undefined
        }
      >
        {children}
      </ScrollView>
    );
  }

  return (
    <View style={[baseStyle, style]}>
      {children}
    </View>
  );
};

const styles = StyleSheet.create({
  scroll: {
    flex: 1,
    backgroundColor: theme.colors.background,
  },
  scrollContent: {
    paddingBottom: theme.spacing.xxl, // Extra space at bottom for safe area
  },
});
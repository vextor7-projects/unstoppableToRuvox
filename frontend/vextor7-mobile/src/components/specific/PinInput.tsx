import React from 'react';
import { View, StyleSheet } from 'react-native';
import { theme } from '@/styles/theme';

interface PinInputProps {
  length?: number;
  value: string;
}

export const PinInput: React.FC<PinInputProps> = ({ length = 6, value }) => {
  return (
    <View style={styles.container}>
      {Array.from({ length }).map((_, index) => {
        const isFilled = index < value.length;
        return (
          <View
            key={index}
            style={[
              styles.dot,
              isFilled ? styles.dotFilled : styles.dotEmpty,
            ]}
          />
        );
      })}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    gap: theme.spacing.l,
    marginVertical: theme.spacing.xl,
  },
  dot: {
    width: 16,
    height: 16,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: theme.colors.primary,
  },
  dotFilled: {
    backgroundColor: theme.colors.primary,
  },
  dotEmpty: {
    backgroundColor: 'transparent',
  },
});
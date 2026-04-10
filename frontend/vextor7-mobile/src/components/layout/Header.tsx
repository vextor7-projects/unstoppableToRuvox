import React from 'react';
import { View, StyleSheet, TouchableOpacity } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { theme } from '@/styles/theme';
import { Typography } from '@/components/common/Typography';
import { Icon, IconName } from '@/components/common/Icon';

interface HeaderProps {
  title?: string;
  showBack?: boolean;
  onBack?: () => void;
  rightIcon?: IconName;
  onRightPress?: () => void;
  transparent?: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  title,
  showBack = true,
  onBack,
  rightIcon,
  onRightPress,
  transparent = false,
}) => {
  const navigation = useNavigation();

  const handleBack = () => {
    if (onBack) {
      onBack();
    } else if (navigation.canGoBack()) {
      navigation.goBack();
    }
  };

  return (
    <View style={[styles.container, !transparent && { backgroundColor: theme.colors.background, borderBottomWidth: 1, borderBottomColor: theme.colors.divider }]}>
      <View style={styles.leftContainer}>
        {showBack ? (
          <TouchableOpacity onPress={handleBack} style={styles.iconButton}>
            <Icon name="arrow-left" size={24} color={theme.colors.textPrimary} />
          </TouchableOpacity>
        ) : null}
      </View>
      
      <View style={styles.centerContainer}>
        {title ? (
          <Typography variant="h3" weight="bold" align="center">
            {title}
          </Typography>
        ) : null}
      </View>

      <View style={styles.rightContainer}>
        {rightIcon ? (
          <TouchableOpacity onPress={onRightPress} style={styles.iconButton}>
            <Icon name={rightIcon} size={24} color={theme.colors.primary} />
          </TouchableOpacity>
        ) : null}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: { height: theme.layout.headerHeight, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingHorizontal: theme.spacing.m, width: '100%', zIndex: 10 },
  leftContainer: { width: 40, alignItems: 'flex-start' },
  centerContainer: { flex: 1, alignItems: 'center' },
  rightContainer: { width: 40, alignItems: 'flex-end' },
  iconButton: { padding: 8 },
});
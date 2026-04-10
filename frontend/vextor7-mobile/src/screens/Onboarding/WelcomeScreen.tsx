import React, { useState, useRef } from 'react';
import { View, StyleSheet, FlatList, Dimensions, NativeSyntheticEvent, NativeScrollEvent } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { AuthStackParamList } from '@/types/navigation';
import { SafeAreaViewWrapper } from '@/components/layout/SafeAreaViewWrapper';
import { Button } from '@/components/common/Button';
import { Typography } from '@/components/common/Typography';
import { Icon } from '@/components/common/Icon';
import { theme } from '@/styles/theme';

const { width } = Dimensions.get('window');

const SLIDES = [
  {
    id: '1',
    title: 'Multi-Chain Support',
    description: 'Access multiple blockchains seamlessly. Manage Bitcoin, Ethereum, and other cryptocurrencies in one place.',
    icon: 'link' as const,
  },
  {
    id: '2',
    title: 'Non-Custodial Security',
    description: 'You control your keys, you control your crypto. Your assets remain secure with industry-leading encryption.',
    icon: 'shield' as const,
  },
  {
    id: '3',
    title: 'Instant Payments',
    description: 'Transfer funds instantly and stay in control of your money at all times.',
    icon: 'zap' as const,
  },
];

type WelcomeScreenNavigationProp = NativeStackNavigationProp<AuthStackParamList, 'Welcome'>;

export default function WelcomeScreen() {
  const navigation = useNavigation<WelcomeScreenNavigationProp>();
  const [currentIndex, setCurrentIndex] = useState(0);
  const flatListRef = useRef<FlatList>(null);

  const handleScroll = (event: NativeSyntheticEvent<NativeScrollEvent>) => {
    const scrollPosition = event.nativeEvent.contentOffset.x;
    const index = Math.round(scrollPosition / width);
    setCurrentIndex(index);
  };

  return (
    <SafeAreaViewWrapper isRoot>
      <View style={styles.container}>
        <View style={styles.skipContainer}>
          <Typography 
            variant="button" 
            color={theme.colors.textSecondary} 
            onPress={() => navigation.navigate('Login')}
          >
            Skip
          </Typography>
        </View>

        <FlatList
          ref={flatListRef}
          data={SLIDES}
          keyExtractor={(item) => item.id}
          horizontal
          pagingEnabled
          showsHorizontalScrollIndicator={false}
          onScroll={handleScroll}
          scrollEventThrottle={16}
          renderItem={({ item }) => (
            <View style={styles.slide}>
              <View style={styles.iconContainer}>
                <Icon name={item.icon} size={64} color={theme.colors.textInverse} />
              </View>
              <Typography variant="h2" weight="bold" align="center" style={styles.title}>
                {item.title}
              </Typography>
              <Typography variant="body" color={theme.colors.textSecondary} align="center" style={styles.description}>
                {item.description}
              </Typography>
            </View>
          )}
        />

        <View style={styles.pagination}>
          {SLIDES.map((_, index) => (
            <View
              key={index}
              style={[
                styles.dot,
                currentIndex === index ? styles.activeDot : styles.inactiveDot,
              ]}
            />
          ))}
        </View>

        <View style={styles.footer}>
          <Button 
            title="Create Account" 
            onPress={() => navigation.navigate('Register')} 
            style={{ marginBottom: theme.spacing.m }}
          />
          <Button 
            title="Log In" 
            variant="outline" 
            onPress={() => navigation.navigate('Login')} 
          />
        </View>
      </View>
    </SafeAreaViewWrapper>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  skipContainer: { alignItems: 'flex-end', padding: theme.spacing.l },
  slide: { width, alignItems: 'center', justifyContent: 'center', paddingHorizontal: theme.spacing.xl },
  iconContainer: { 
    width: 120, height: 120, borderRadius: 32, 
    backgroundColor: theme.colors.primary, 
    alignItems: 'center', justifyContent: 'center', 
    marginBottom: theme.spacing.xl 
  },
  title: { marginBottom: theme.spacing.m },
  description: { lineHeight: 24, paddingHorizontal: theme.spacing.m },
  pagination: { flexDirection: 'row', justifyContent: 'center', marginBottom: theme.spacing.xl },
  dot: { width: 8, height: 8, borderRadius: 4, marginHorizontal: 4 },
  activeDot: { backgroundColor: theme.colors.primary, width: 24 },
  inactiveDot: { backgroundColor: theme.colors.border },
  footer: { padding: theme.spacing.l, paddingBottom: theme.spacing.xxl },
});
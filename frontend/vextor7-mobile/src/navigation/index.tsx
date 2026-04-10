import React from 'react';
import { NavigationContainer, DefaultTheme } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { StatusBar } from 'expo-status-bar';
import { useAuth } from '@/hooks/useAuth';
import { theme } from '@/styles/theme';
import { RootStackParamList } from '@/types/navigation';


// Stacks
import { AuthStack } from './AuthStack';
import { MainTabNavigator } from './MainTabNavigator';

// Placeholder Splash
import { View, ActivityIndicator } from 'react-native';

const Stack = createNativeStackNavigator<RootStackParamList>();

const SplashScreen = () => (
  <View style={{ flex: 1, backgroundColor: theme.colors.background, justifyContent: 'center', alignItems: 'center' }}>
    <ActivityIndicator size="large" color={theme.colors.primary} />
  </View>
);

export const RootNavigator = () => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return <SplashScreen />;
  }

  return (
    <NavigationContainer theme={{
      dark: true,
      colors: {
        primary: theme.colors.primary,
        background: theme.colors.background,
        card: theme.colors.backgroundSecondary,
        text: theme.colors.textPrimary,
        border: theme.colors.border,
        notification: theme.colors.error,
      },
      fonts: DefaultTheme.fonts,
    }}>
      <StatusBar style="light" backgroundColor={theme.colors.background} />
      <Stack.Navigator screenOptions={{ headerShown: false }}>
        {isAuthenticated ? (
          <Stack.Screen name="Main" component={MainTabNavigator} />
        ) : (
          <Stack.Screen name="Auth" component={AuthStack} />
        )}
      </Stack.Navigator>
    </NavigationContainer>
  );
};
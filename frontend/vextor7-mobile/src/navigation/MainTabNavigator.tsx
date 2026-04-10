import React from 'react';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { MainTabParamList } from '@/types/navigation';
import { theme } from '@/styles/theme';
import { Icon } from '@/components/common/Icon';
import { Platform, View } from 'react-native';

import WalletHomeScreen from '@/screens/Wallet/WalletHomeScreen';
import SwapScreen from '@/screens/Swap/SwapScreen';
import PaymentsScreen from '@/screens/Payments/PaymentsScreen';
import MarketScreen from '@/screens/Market/MarketScreen';
import SettingsScreen from '@/screens/Settings/SettingsScreen';

const Tab = createBottomTabNavigator<MainTabParamList>();

export const MainTabNavigator = () => {
  return (
    <Tab.Navigator
      screenOptions={{
        headerShown: false,
        tabBarStyle: {
          backgroundColor: theme.colors.backgroundSecondary,
          borderTopColor: theme.colors.border,
          borderTopWidth: 0.5,
          height: theme.layout.bottomTabHeight,
          paddingTop: 8,
          paddingBottom: Platform.OS === 'ios' ? 24 : 8,
        },
        tabBarActiveTintColor: theme.colors.primary,
        tabBarInactiveTintColor: theme.colors.textSecondary,
        tabBarLabelStyle: {
          fontSize: 10,
          marginBottom: 4,
        },
      }}
    >
      <Tab.Screen 
        name="WalletTab" 
        component={WalletHomeScreen} 
        options={{
          tabBarLabel: 'Wallet',
          tabBarIcon: ({ color, size }) => <Icon name="credit-card" size={size} color={color} />,
        }}
      />
      <Tab.Screen 
        name="SwapTab" 
        component={SwapScreen}
        options={{
          tabBarLabel: 'Swap',
          tabBarIcon: ({ color, size }) => <Icon name="repeat" size={size} color={color} />,
        }}
      />
      <Tab.Screen 
        name="PayTab" 
        component={PaymentsScreen}
        options={{
          tabBarLabel: 'Pay',
          tabBarIcon: ({ color }) => (
            <View style={{
              marginTop: -20,
              backgroundColor: theme.colors.primary,
              padding: 12,
              borderRadius: 30,
              shadowColor: theme.colors.primary,
              shadowOffset: { width: 0, height: 4 },
              shadowOpacity: 0.5,
              shadowRadius: 8,
            }}>
              <Icon name="scan" size={24} color="#FFF" />
            </View>
          ),
        }}
      />
      <Tab.Screen 
        name="MarketTab" 
        component={MarketScreen} 
        options={{
          tabBarLabel: 'Market',
          tabBarIcon: ({ color, size }) => <Icon name="bar-chart-2" size={size} color={color} />,
        }}
      />
      <Tab.Screen 
        name="SettingsTab" 
        component={SettingsScreen} 
        options={{
          tabBarLabel: 'Settings',
          tabBarIcon: ({ color, size }) => <Icon name="settings" size={size} color={color} />,
        }}
      />
    </Tab.Navigator>
  );
};
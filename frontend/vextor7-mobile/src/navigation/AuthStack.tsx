import React from 'react';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { AuthStackParamList } from '@/types/navigation';
import { theme } from '@/styles/theme';

// Placeholder imports for screens we will write in the next batch
// In a real IDE, these would be red until the file is created.
// For now, I assume they map to the requested screen folder structure.
import WelcomeScreen from '@/screens/Onboarding/WelcomeScreen';
import LoginScreen from '@/screens/Auth/LoginScreen';
import RegisterScreen from '@/screens/Auth/RegisterScreen';
import PinScreen from '@/screens/Auth/PinScreen';
import SeedPhraseScreen from '@/screens/Auth/SeedPhraseScreen';

const Stack = createNativeStackNavigator<AuthStackParamList>();

export const AuthStack = () => {
  return (
    <Stack.Navigator
      screenOptions={{
        headerShown: false,
        contentStyle: { backgroundColor: theme.colors.background },
        animation: 'slide_from_right',
      }}
    >
      <Stack.Screen name="Welcome" component={WelcomeScreen} />
      <Stack.Screen name="Login" component={LoginScreen} />
      <Stack.Screen name="Register" component={RegisterScreen} />
      <Stack.Screen name="PinSetup" component={PinScreen} />
      <Stack.Screen name="RecoveryPhrase" component={SeedPhraseScreen} />
    </Stack.Navigator>
  );
};
import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { useFonts } from 'expo-font';
import { PlayfairDisplay_400Regular } from '@expo-google-fonts/playfair-display';
import { CedarvilleCursive_400Regular } from '@expo-google-fonts/cedarville-cursive';
import { LinearGradient } from 'expo-linear-gradient';
import { SafeAreaView, SafeAreaProvider } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { theme } from './theme';
import InterviewScreen from './screens/InterviewScreen';
import CalendarScreen from './screens/CalendarScreen'
import MagazineScreen from './screens/MagazineScreen';
import FeaturedScreen from './screens/FeaturedScreen';

const Tab = createBottomTabNavigator();

export default function App() {
  const [fontsLoaded] = useFonts({
    'PlayfairDisplay-Regular': PlayfairDisplay_400Regular,
    'CedarvilleCursive-Regular': CedarvilleCursive_400Regular,
  });

  if (!fontsLoaded) return null;

  return (
    <LinearGradient
      colors={[theme.colors.cloudDancer, theme.colors.silkyEnd]}
      start={{ x: 0, y: 0 }}
      end={{ x: 1, y: 1 }}
      style={{ flex: 1 }}
    >
      <SafeAreaProvider>
        <SafeAreaView style={{ flex: 1, backgroundColor: 'transparent' }} edges={['top', 'bottom']}>
          <NavigationContainer>
            <Tab.Navigator
              screenOptions={({ route }) => ({
                headerShown: false,
                tabBarStyle: {
                  backgroundColor: theme.colors.deepBlack,
                  borderTopWidth: 1,
                  borderTopColor: theme.colors.spineGold,
                  height: 70,
                  paddingTop: 6,
                  paddingBottom: 10,
                },
                tabBarActiveTintColor: theme.colors.spineGold,
                tabBarInactiveTintColor: '#999',
                tabBarLabelStyle: {
                  fontFamily: 'PlayfairDisplay-Regular',
                  fontSize: 11,
                  letterSpacing: 0.5,
                },
                tabBarIcon: ({ color, size }) => {
                  const iconMap: Record<string, keyof typeof Ionicons.glyphMap> = {
                    Interview: 'create-outline',
                    Calendar: 'book-outline',
                    Magazine: 'sparkles-outline',
                    Featured: 'pricetag-outline',
                  };
                  return <Ionicons name={iconMap[route.name] ?? 'ellipse'} size={22} color={color} />;
                },
              })}
            >
              <Tab.Screen name="Interview" component={InterviewScreen} />
              <Tab.Screen name="Calendar" component={CalendarScreen} />
              <Tab.Screen name="Magazine" component={MagazineScreen} options={{ tabBarLabel: 'The Magazine' }} />
              <Tab.Screen name="Featured" component={FeaturedScreen} />
            </Tab.Navigator>
          </NavigationContainer>
        </SafeAreaView>
      </SafeAreaProvider>
    </LinearGradient>
  );
}
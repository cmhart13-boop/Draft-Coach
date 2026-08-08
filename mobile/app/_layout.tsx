import { Tabs } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { Platform } from 'react-native';

const active = '#dfff00';
const inactive = '#a8b0b8';
const background = '#070b0f';

export default function RootLayout() {
  return (
    <>
      <StatusBar style="light" />
      <Tabs
        screenOptions={{
          headerShown: false,
          tabBarActiveTintColor: active,
          tabBarInactiveTintColor: inactive,
          tabBarStyle: {
            backgroundColor: background,
            borderTopColor: '#263540',
            height: Platform.OS === 'ios' ? 88 : 72,
            paddingTop: 8,
            paddingBottom: Platform.OS === 'ios' ? 24 : 10,
          },
          tabBarLabelStyle: {
            fontSize: 11,
            fontWeight: '800',
          },
        }}
      >
        <Tabs.Screen name="index" options={{ title: 'Home' }} />
        <Tabs.Screen name="draft" options={{ title: 'Draft' }} />
        <Tabs.Screen name="players" options={{ title: 'Players' }} />
        <Tabs.Screen name="team-iq" options={{ title: 'Team IQ' }} />
        <Tabs.Screen name="coach" options={{ title: 'Coach' }} />
      </Tabs>
    </>
  );
}

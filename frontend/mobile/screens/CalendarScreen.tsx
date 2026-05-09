// frontend/mobile/screens/CalendarScreen.tsx
import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { theme } from '../theme';

export default function CalendarScreen() {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>📖 Calendar</Text>
      <Text style={styles.subtitle}>Your week's pages — coming soon</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 24,
  },
  title: {
    fontSize: 28,
    fontFamily: 'PlayfairDisplay-Regular',
    color: theme.colors.deepBlack,
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 14,
    color: '#666',
    fontStyle: 'italic',
  },
});
import { Pressable, SafeAreaView, ScrollView, StyleSheet, Text, View } from 'react-native';
import { router } from 'expo-router';

const actions = [
  ['Mock Draft', '/draft'],
  ['Players', '/players'],
  ['Team IQ', '/team-iq'],
  ['Draft Coach', '/coach'],
] as const;

export default function HomeScreen() {
  return (
    <SafeAreaView style={styles.safe}>
      <ScrollView contentContainerStyle={styles.container}>
        <Text style={styles.eyebrow}>SHIVA INTELLIGENCE</Text>
        <Text style={styles.title}>Fantasy football built for your phone.</Text>
        <Text style={styles.subtitle}>Draft faster, open any player instantly, and keep every decision in one connected mobile workflow.</Text>
        <View style={styles.grid}>
          {actions.map(([label, path]) => (
            <Pressable key={label} onPress={() => router.push(path)} style={({ pressed }) => [styles.card, pressed && styles.pressed]}>
              <Text style={styles.cardText}>{label}</Text>
            </Pressable>
          ))}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: '#070b0f' },
  container: { padding: 20, gap: 14 },
  eyebrow: { color: '#dfff00', fontSize: 12, fontWeight: '900', letterSpacing: 1.4 },
  title: { color: '#ffffff', fontSize: 32, lineHeight: 36, fontWeight: '900' },
  subtitle: { color: '#aeb6bf', fontSize: 16, lineHeight: 23 },
  grid: { gap: 12, marginTop: 8 },
  card: { minHeight: 88, borderRadius: 18, padding: 18, justifyContent: 'center', backgroundColor: '#121920', borderWidth: 1, borderColor: '#263540' },
  pressed: { opacity: 0.72 },
  cardText: { color: '#ffffff', fontSize: 19, fontWeight: '850' },
});

import { SafeAreaView, StyleSheet, Text, View } from 'react-native';

export default function CoachScreen() {
  return (
    <SafeAreaView style={styles.safe}>
      <View style={styles.container}>
        <Text style={styles.title}>DRAFT COACH</Text>
        <Text style={styles.copy}>Live recommendations will use verified board data, roster construction, scarcity, next-pick availability, historical risk, and weekly usability through the shared backend engine.</Text>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: '#070b0f' },
  container: { padding: 16, gap: 12 },
  title: { color: '#fff', fontSize: 26, fontWeight: '900' },
  copy: { color: '#aeb6bf', fontSize: 15, lineHeight: 22 },
});

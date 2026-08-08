import { SafeAreaView, StyleSheet, Text, View } from 'react-native';

export default function TeamIQScreen() {
  return (
    <SafeAreaView style={styles.safe}>
      <View style={styles.container}>
        <Text style={styles.title}>TEAM IQ</Text>
        <Text style={styles.copy}>League history, manager tendencies, draft ROI, and season filters will be designed as native mobile cards and sheets rather than compressed web tables.</Text>
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

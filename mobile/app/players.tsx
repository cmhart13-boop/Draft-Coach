import { SafeAreaView, StyleSheet, Text, TextInput, View } from 'react-native';

export default function PlayersScreen() {
  return (
    <SafeAreaView style={styles.safe}>
      <View style={styles.container}>
        <Text style={styles.title}>PLAYERS</Text>
        <TextInput placeholder="Search players..." placeholderTextColor="#74808a" style={styles.search} />
        <Text style={styles.copy}>Native player search will open the same canonical player profile from every screen in the app.</Text>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: '#070b0f' },
  container: { padding: 16, gap: 14 },
  title: { color: '#fff', fontSize: 26, fontWeight: '900' },
  search: { minHeight: 50, borderRadius: 14, paddingHorizontal: 16, color: '#fff', fontSize: 17, backgroundColor: '#121920', borderWidth: 1, borderColor: '#263540' },
  copy: { color: '#aeb6bf', fontSize: 15, lineHeight: 22 },
});

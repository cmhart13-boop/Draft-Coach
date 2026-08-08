import { SafeAreaView, ScrollView, StyleSheet, Text, View } from 'react-native';

const tabs = ['Players', 'Queue', 'Draft Board', 'Roster'];

export default function DraftScreen() {
  return (
    <SafeAreaView style={styles.safe}>
      <View style={styles.header}>
        <Text style={styles.title}>MOCK DRAFT</Text>
        <Text style={styles.meta}>10-Team • Full PPR • 2026</Text>
      </View>
      <View style={styles.tabs}>{tabs.map((tab, i) => <View key={tab} style={[styles.tab, i === 0 && styles.activeTab]}><Text style={[styles.tabText, i === 0 && styles.activeText]}>{tab}</Text></View>)}</View>
      <ScrollView contentContainerStyle={styles.content}>
        <Text style={styles.section}>Players Available</Text>
        <Text style={styles.help}>This native screen will consume the shared Python draft engine through the mobile API. Queue, board, roster, filters, and live draft state will stay synchronized without page resets.</Text>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: '#070b0f' },
  header: { paddingHorizontal: 16, paddingTop: 12, paddingBottom: 10 },
  title: { color: '#fff', fontSize: 26, fontWeight: '900' },
  meta: { color: '#9ea8b1', fontSize: 13, marginTop: 3 },
  tabs: { flexDirection: 'row', borderBottomWidth: 1, borderBottomColor: '#263540' },
  tab: { flex: 1, minHeight: 48, alignItems: 'center', justifyContent: 'center' },
  activeTab: { borderBottomWidth: 3, borderBottomColor: '#dfff00' },
  tabText: { color: '#89939d', fontSize: 11, fontWeight: '800' },
  activeText: { color: '#fff' },
  content: { padding: 16, gap: 12 },
  section: { color: '#fff', fontSize: 20, fontWeight: '900' },
  help: { color: '#aeb6bf', fontSize: 15, lineHeight: 22 },
});

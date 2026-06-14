import { useCallback, useEffect, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  FlatList,
  Pressable,
  RefreshControl,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { useFocusEffect } from 'expo-router';
import * as DocumentPicker from 'expo-document-picker';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useAuth } from '@/context/AuthContext';
import { InspectionCard } from '@/components/InspectionCard';
import { ImportModal } from '@/components/ImportModal';
import { colors, radii, spacing, typography } from '@/theme/colors';
import { dayKey, formatDayHeading } from '@/lib/datetime';
import { parseIcs, type ParsedEvent } from '@/lib/ics';
import { readFileText } from '@/lib/fileText';
import {
  deleteInspection,
  importEvents,
  listInspections,
} from '@/services/inspections';
import {
  detectClashes,
  sortByStart,
  travelPairs,
  type Clash,
} from '@/lib/clashDetection';
import { getTravelMinutes } from '@/services/travelTime';
import type { Inspection } from '@/types/database';

type Row =
  | { kind: 'header'; key: string; title: string }
  | { kind: 'item'; key: string; inspection: Inspection };

export default function ScheduleScreen() {
  const { user } = useAuth();
  const insets = useSafeAreaInsets();

  const [inspections, setInspections] = useState<Inspection[]>([]);
  const [clashes, setClashes] = useState<Map<string, Clash>>(new Map());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [pickedEvents, setPickedEvents] = useState<ParsedEvent[] | null>(null);
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    setError(null);
    try {
      const data = await listInspections();
      setInspections(data);
      // First pass: clashes from overlaps + gap heuristic (instant).
      setClashes(detectClashes(data, new Map()));
      // Second pass: refine with travel times where a provider is available.
      void refineWithTravelTimes(data, setClashes);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load schedule');
    } finally {
      setLoading(false);
    }
  }, []);

  useFocusEffect(
    useCallback(() => {
      load();
    }, [load]),
  );

  async function onPickFile() {
    try {
      const result = await DocumentPicker.getDocumentAsync({
        type: ['text/calendar', 'application/octet-stream', '*/*'],
        copyToCacheDirectory: true,
        multiple: false,
      });
      if (result.canceled || !result.assets?.[0]) return;
      const text = await readFileText(result.assets[0].uri);
      const events = parseIcs(text);
      setPickedEvents(events);
    } catch {
      Alert.alert('Import failed', "Couldn't read that file. Please try a valid .ics invite.");
    }
  }

  async function onConfirmImport(selected: ParsedEvent[]) {
    if (!user) return;
    setSaving(true);
    try {
      const { inserted, skipped } = await importEvents(user.id, selected, inspections);
      setPickedEvents(null);
      await load();
      const parts = [`Added ${inserted}`];
      if (skipped > 0) parts.push(`${skipped} already on schedule`);
      Alert.alert('Imported', parts.join(' · '));
    } catch (e) {
      Alert.alert('Save failed', e instanceof Error ? e.message : 'Please try again.');
    } finally {
      setSaving(false);
    }
  }

  function onLongPress(inspection: Inspection) {
    Alert.alert('Remove inspection', inspection.address, [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Remove',
        style: 'destructive',
        onPress: async () => {
          try {
            await deleteInspection(inspection.id);
            await load();
          } catch (e) {
            Alert.alert('Delete failed', e instanceof Error ? e.message : 'Please try again.');
          }
        },
      },
    ]);
  }

  const rows = buildRows(inspections);

  return (
    <View style={styles.flex}>
      <View style={[styles.toolbar, { paddingTop: spacing.sm }]}>
        <Text style={styles.count}>
          {inspections.length} inspection{inspections.length === 1 ? '' : 's'}
        </Text>
        <Pressable
          onPress={onPickFile}
          style={({ pressed }) => [styles.importBtn, pressed && { opacity: 0.85 }]}
        >
          <Text style={styles.importBtnText}>＋ Import .ics</Text>
        </Pressable>
      </View>

      {loading ? (
        <View style={styles.center}>
          <ActivityIndicator color={colors.amber} size="large" />
        </View>
      ) : error ? (
        <View style={styles.center}>
          <Text style={styles.errorText}>{error}</Text>
          <Pressable onPress={load} hitSlop={8}>
            <Text style={styles.retry}>Tap to retry</Text>
          </Pressable>
        </View>
      ) : rows.length === 0 ? (
        <View style={styles.center}>
          <Text style={styles.emptyTitle}>No inspections yet</Text>
          <Text style={styles.emptyBody}>
            Import a calendar invite (.ics) from REA or Domain to add open homes to
            your schedule.
          </Text>
          <Pressable
            onPress={onPickFile}
            style={({ pressed }) => [styles.emptyBtn, pressed && { opacity: 0.85 }]}
          >
            <Text style={styles.emptyBtnText}>Import .ics file</Text>
          </Pressable>
        </View>
      ) : (
        <FlatList
          data={rows}
          keyExtractor={(r) => r.key}
          contentContainerStyle={{ padding: spacing.lg, paddingBottom: insets.bottom + spacing.xl }}
          refreshControl={
            <RefreshControl refreshing={loading} onRefresh={load} tintColor={colors.amber} />
          }
          renderItem={({ item }) =>
            item.kind === 'header' ? (
              <Text style={styles.dayHeading}>{item.title}</Text>
            ) : (
              <Pressable
                onLongPress={() => onLongPress(item.inspection)}
                delayLongPress={350}
              >
                <InspectionCard
                  inspection={item.inspection}
                  clash={clashes.get(item.inspection.id)}
                />
              </Pressable>
            )
          }
        />
      )}

      <ImportModal
        visible={pickedEvents !== null}
        events={pickedEvents ?? []}
        saving={saving}
        onCancel={() => setPickedEvents(null)}
        onConfirm={onConfirmImport}
      />
    </View>
  );
}

/** Fetch travel times for same-day pairs and recompute clashes. */
async function refineWithTravelTimes(
  data: Inspection[],
  setClashes: (c: Map<string, Clash>) => void,
) {
  const pairs = travelPairs(data);
  if (pairs.length === 0) return;
  const travelByDestId = new Map<string, number>();
  await Promise.all(
    pairs.map(async (p) => {
      const mins = await getTravelMinutes(p.origin, p.destination);
      if (mins != null) travelByDestId.set(p.destId, mins);
    }),
  );
  if (travelByDestId.size > 0) {
    setClashes(detectClashes(data, travelByDestId));
  }
}

/** Flatten sorted inspections into day-grouped header/item rows. */
function buildRows(inspections: Inspection[]): Row[] {
  const sorted = sortByStart(inspections);
  const noTime = inspections.filter((i) => !i.schedule_time);
  const rows: Row[] = [];
  let currentDay = '';

  for (const insp of sorted) {
    const d = new Date(insp.schedule_time!);
    const key = dayKey(d);
    if (key !== currentDay) {
      currentDay = key;
      rows.push({ kind: 'header', key: `h-${key}`, title: formatDayHeading(d) });
    }
    rows.push({ kind: 'item', key: insp.id, inspection: insp });
  }

  if (noTime.length > 0) {
    rows.push({ kind: 'header', key: 'h-untimed', title: 'No time set' });
    for (const insp of noTime) {
      rows.push({ kind: 'item', key: insp.id, inspection: insp });
    }
  }

  return rows;
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: colors.navy },
  toolbar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: spacing.lg,
    paddingBottom: spacing.sm,
  },
  count: { ...typography.caption, color: colors.textSecondary },
  importBtn: {
    backgroundColor: colors.navyCard,
    borderColor: colors.amber,
    borderWidth: 1,
    borderRadius: radii.pill,
    paddingHorizontal: spacing.md,
    paddingVertical: 8,
  },
  importBtnText: { color: colors.amberSoft, fontWeight: '700', fontSize: 13 },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: spacing.xl },
  errorText: { color: colors.danger, textAlign: 'center', marginBottom: spacing.sm },
  retry: { color: colors.amberSoft, fontWeight: '600' },
  emptyTitle: { ...typography.heading, color: colors.textPrimary, marginBottom: spacing.sm },
  emptyBody: {
    ...typography.body,
    color: colors.textSecondary,
    textAlign: 'center',
    lineHeight: 22,
    marginBottom: spacing.lg,
  },
  emptyBtn: {
    backgroundColor: colors.amber,
    borderRadius: radii.md,
    paddingHorizontal: spacing.lg,
    paddingVertical: 12,
  },
  emptyBtnText: { color: colors.navy, fontWeight: '700' },
  dayHeading: {
    ...typography.subheading,
    color: colors.textSecondary,
    marginBottom: spacing.sm,
    marginTop: spacing.sm,
  },
});

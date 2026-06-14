import { useState } from 'react';
import {
  Modal,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { PrimaryButton } from '@/components/ui';
import { colors, radii, spacing, typography } from '@/theme/colors';
import { formatDayHeading, formatTime } from '@/lib/datetime';
import type { ParsedEvent } from '@/lib/ics';

/**
 * Preview parsed .ics events before saving. Each event can be toggled off;
 * confirming imports the selected ones.
 */
export function ImportModal({
  visible,
  events,
  saving,
  onCancel,
  onConfirm,
}: {
  visible: boolean;
  events: ParsedEvent[];
  saving: boolean;
  onCancel: () => void;
  onConfirm: (selected: ParsedEvent[]) => void;
}) {
  const [excluded, setExcluded] = useState<Set<number>>(new Set());

  function toggle(idx: number) {
    setExcluded((prev) => {
      const next = new Set(prev);
      if (next.has(idx)) next.delete(idx);
      else next.add(idx);
      return next;
    });
  }

  const selected = events.filter((_, i) => !excluded.has(i));

  return (
    <Modal visible={visible} animationType="slide" transparent onRequestClose={onCancel}>
      <View style={styles.backdrop}>
        <View style={styles.sheet}>
          <Text style={styles.title}>
            {events.length === 0
              ? 'No inspections found'
              : `Found ${events.length} inspection${events.length === 1 ? '' : 's'}`}
          </Text>

          {events.length === 0 ? (
            <Text style={styles.empty}>
              We couldn't read any calendar events from that file. Make sure it's a
              valid .ics invite from REA or Domain.
            </Text>
          ) : (
            <ScrollView style={styles.list} contentContainerStyle={{ paddingBottom: spacing.sm }}>
              {events.map((ev, i) => {
                const on = !excluded.has(i);
                return (
                  <Pressable
                    key={`${ev.uid ?? ev.address}-${i}`}
                    onPress={() => toggle(i)}
                    style={[styles.row, !on && styles.rowOff]}
                  >
                    <View style={[styles.check, on && styles.checkOn]}>
                      {on ? <Text style={styles.checkMark}>✓</Text> : null}
                    </View>
                    <View style={styles.rowBody}>
                      <Text style={styles.rowAddr} numberOfLines={2}>
                        {ev.address}
                      </Text>
                      <Text style={styles.rowMeta}>
                        {formatDayHeading(ev.start)} · {formatTime(ev.start)}
                        {ev.listingUrl ? '  ·  🔗 listing' : ''}
                      </Text>
                    </View>
                  </Pressable>
                );
              })}
            </ScrollView>
          )}

          <View style={styles.actions}>
            {events.length > 0 ? (
              <PrimaryButton
                label={saving ? 'Saving…' : `Add ${selected.length} to schedule`}
                onPress={() => onConfirm(selected)}
                loading={saving}
                disabled={selected.length === 0}
              />
            ) : null}
            <Pressable onPress={onCancel} hitSlop={8} disabled={saving}>
              <Text style={styles.cancel}>Cancel</Text>
            </Pressable>
          </View>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  backdrop: { flex: 1, backgroundColor: colors.overlay, justifyContent: 'flex-end' },
  sheet: {
    backgroundColor: colors.navyElevated,
    borderTopLeftRadius: radii.lg,
    borderTopRightRadius: radii.lg,
    padding: spacing.lg,
    maxHeight: '80%',
  },
  title: { ...typography.heading, color: colors.textPrimary, marginBottom: spacing.md },
  empty: { ...typography.body, color: colors.textSecondary, lineHeight: 22, marginBottom: spacing.md },
  list: { flexGrow: 0 },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.navyCard,
    borderRadius: radii.md,
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.md,
    marginBottom: spacing.sm,
  },
  rowOff: { opacity: 0.45 },
  check: {
    width: 22,
    height: 22,
    borderRadius: 6,
    borderWidth: 2,
    borderColor: colors.textMuted,
    marginRight: spacing.md,
    alignItems: 'center',
    justifyContent: 'center',
  },
  checkOn: { backgroundColor: colors.amber, borderColor: colors.amber },
  checkMark: { color: colors.navy, fontSize: 14, fontWeight: '800' },
  rowBody: { flex: 1 },
  rowAddr: { ...typography.body, color: colors.textPrimary },
  rowMeta: { ...typography.caption, color: colors.textSecondary, marginTop: 2 },
  actions: { marginTop: spacing.sm },
  cancel: { color: colors.textSecondary, textAlign: 'center', paddingVertical: spacing.md, fontWeight: '600' },
});

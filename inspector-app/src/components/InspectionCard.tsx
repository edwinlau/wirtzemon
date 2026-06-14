import { StyleSheet, Text, View } from 'react-native';
import { colors, radii, spacing, typography } from '@/theme/colors';
import { formatTime } from '@/lib/datetime';
import type { Clash } from '@/lib/clashDetection';
import type { Inspection, InspectionStatus } from '@/types/database';

const STATUS_META: Record<InspectionStatus, { label: string; color: string }> = {
  upcoming: { label: 'Upcoming', color: colors.info },
  in_progress: { label: 'In progress', color: colors.amber },
  done: { label: 'Done', color: colors.success },
};

export function InspectionCard({
  inspection,
  clash,
}: {
  inspection: Inspection;
  clash?: Clash;
}) {
  const status = STATUS_META[inspection.status];
  const time = inspection.schedule_time
    ? formatTime(new Date(inspection.schedule_time))
    : 'No time set';

  return (
    <View style={styles.card}>
      <View style={styles.headerRow}>
        <Text style={styles.time}>{time}</Text>
        <View style={[styles.badge, { borderColor: status.color }]}>
          <View style={[styles.dot, { backgroundColor: status.color }]} />
          <Text style={[styles.badgeText, { color: status.color }]}>{status.label}</Text>
        </View>
      </View>

      <Text style={styles.address} numberOfLines={2}>
        {inspection.address}
      </Text>

      {inspection.listing_url ? (
        <Text style={styles.listing} numberOfLines={1}>
          {inspection.listing_url.replace(/^https?:\/\/(www\.)?/, '')}
        </Text>
      ) : null}

      {clash ? (
        <View style={styles.warning}>
          <Text style={styles.warningIcon}>{clash.type === 'overlap' ? '⛔' : '⚠️'}</Text>
          <Text style={styles.warningText}>{clash.message}</Text>
        </View>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.navyCard,
    borderRadius: radii.lg,
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.md,
    marginBottom: spacing.md,
  },
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.sm,
  },
  time: { ...typography.subheading, color: colors.textPrimary },
  badge: {
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1,
    borderRadius: radii.pill,
    paddingHorizontal: spacing.sm,
    paddingVertical: 3,
  },
  dot: { width: 6, height: 6, borderRadius: 3, marginRight: 6 },
  badgeText: { fontSize: 12, fontWeight: '600' },
  address: { ...typography.body, color: colors.textPrimary, lineHeight: 21 },
  listing: { ...typography.caption, color: colors.textMuted, marginTop: spacing.xs },
  warning: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginTop: spacing.sm,
    backgroundColor: colors.navyElevated,
    borderRadius: radii.md,
    borderLeftWidth: 3,
    borderLeftColor: colors.warning,
    padding: spacing.sm,
  },
  warningIcon: { fontSize: 13, marginRight: 6 },
  warningText: { ...typography.caption, color: colors.amberSoft, flex: 1, lineHeight: 18 },
});

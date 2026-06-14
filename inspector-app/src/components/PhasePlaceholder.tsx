import { StyleSheet, Text, View } from 'react-native';
import { Card, Screen } from '@/components/ui';
import { colors, spacing, typography } from '@/theme/colors';

/**
 * Temporary scaffold content for tabs whose features land in later phases.
 * Keeps navigation real and testable before the feature work exists.
 */
export function PhasePlaceholder({
  title,
  phase,
  description,
}: {
  title: string;
  phase: string;
  description: string;
}) {
  return (
    <Screen>
      <Card>
        <Text style={styles.badge}>{phase}</Text>
        <Text style={styles.title}>{title}</Text>
        <Text style={styles.description}>{description}</Text>
      </Card>
    </Screen>
  );
}

const styles = StyleSheet.create({
  badge: {
    ...typography.caption,
    color: colors.amber,
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 1,
    marginBottom: spacing.sm,
  },
  title: { ...typography.heading, color: colors.textPrimary, marginBottom: spacing.sm },
  description: { ...typography.body, color: colors.textSecondary, lineHeight: 22 },
});

import { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, RefreshControl, ScrollView, StyleSheet, Text, View } from 'react-native';
import { useAuth } from '@/context/AuthContext';
import { supabase } from '@/lib/supabase';
import { Card, PrimaryButton } from '@/components/ui';
import { colors, radii, spacing, typography } from '@/theme/colors';
import type { UserProfile } from '@/types/database';

export default function ProfileScreen() {
  const { user, signOut } = useAuth();
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!user) return;
    setError(null);
    const { data, error: err } = await supabase
      .from('users')
      .select('*')
      .eq('id', user.id)
      .maybeSingle();
    if (err) setError(err.message);
    else setProfile(data);
    setLoading(false);
  }, [user]);

  useEffect(() => {
    load();
  }, [load]);

  const badges = profile?.badges ?? [];

  return (
    <ScrollView
      style={styles.flex}
      contentContainerStyle={styles.content}
      refreshControl={
        <RefreshControl refreshing={loading} onRefresh={load} tintColor={colors.amber} />
      }
    >
      <Card>
        <Text style={styles.name}>
          {profile?.display_name ?? user?.email ?? 'Inspector'}
        </Text>
        <Text style={styles.email}>{user?.email}</Text>
      </Card>

      <Card style={styles.spacer}>
        <Text style={styles.sectionLabel}>Contributor score</Text>
        {loading ? (
          <ActivityIndicator color={colors.amber} />
        ) : error ? (
          <Text style={styles.error}>Couldn't load your profile. Pull to retry.</Text>
        ) : (
          <Text style={styles.score}>{profile?.contributor_score ?? 0}</Text>
        )}
        <Text style={styles.hint}>
          Earn points by capturing photos, recording voice notes and completing inspections.
        </Text>
      </Card>

      <Card style={styles.spacer}>
        <Text style={styles.sectionLabel}>Badges</Text>
        {badges.length === 0 ? (
          <Text style={styles.hint}>No badges yet — start inspecting to earn your first.</Text>
        ) : (
          <View style={styles.badgeRow}>
            {badges.map((b) => (
              <View key={b} style={styles.badge}>
                <Text style={styles.badgeText}>{b.replace(/_/g, ' ')}</Text>
              </View>
            ))}
          </View>
        )}
      </Card>

      <View style={styles.spacer}>
        <PrimaryButton label="Sign out" onPress={signOut} />
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: colors.navy },
  content: { padding: spacing.lg },
  spacer: { marginTop: spacing.md },
  name: { ...typography.heading, color: colors.textPrimary },
  email: { ...typography.body, color: colors.textSecondary, marginTop: spacing.xs },
  sectionLabel: {
    ...typography.caption,
    color: colors.textMuted,
    textTransform: 'uppercase',
    letterSpacing: 1,
    marginBottom: spacing.sm,
  },
  score: { fontSize: 40, fontWeight: '800', color: colors.amber },
  hint: { ...typography.caption, color: colors.textSecondary, marginTop: spacing.sm, lineHeight: 18 },
  error: { color: colors.danger },
  badgeRow: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm },
  badge: {
    backgroundColor: colors.navyElevated,
    borderColor: colors.amber,
    borderWidth: 1,
    borderRadius: radii.pill,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs,
  },
  badgeText: { color: colors.amberSoft, fontSize: 13, fontWeight: '600', textTransform: 'capitalize' },
});

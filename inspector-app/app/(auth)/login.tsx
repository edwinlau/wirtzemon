import { useState } from 'react';
import { KeyboardAvoidingView, Platform, ScrollView, StyleSheet, Text, View } from 'react-native';
import { useRouter } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useAuth } from '@/context/AuthContext';
import { Field, LinkButton, PrimaryButton } from '@/components/ui';
import { colors, spacing, typography } from '@/theme/colors';

export default function LoginScreen() {
  const { signIn } = useAuth();
  const router = useRouter();
  const insets = useSafeAreaInsets();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit() {
    setError(null);
    if (!email.trim() || !password) {
      setError('Enter your email and password.');
      return;
    }
    setLoading(true);
    const { error: err } = await signIn(email, password);
    setLoading(false);
    if (err) setError(err);
    // On success the root gatekeeper redirects into the tabs.
  }

  return (
    <KeyboardAvoidingView
      style={styles.flex}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      <ScrollView
        contentContainerStyle={[styles.content, { paddingTop: insets.top + spacing.xl }]}
        keyboardShouldPersistTaps="handled"
      >
        <View style={styles.header}>
          <Text style={styles.brand}>Inspector</Text>
          <Text style={styles.tagline}>Your property inspection companion</Text>
        </View>

        <Text style={styles.title}>Welcome back</Text>

        <Field
          label="Email"
          value={email}
          onChangeText={setEmail}
          autoCapitalize="none"
          autoComplete="email"
          keyboardType="email-address"
          textContentType="emailAddress"
          placeholder="you@example.com"
        />
        <Field
          label="Password"
          value={password}
          onChangeText={setPassword}
          secureTextEntry
          autoComplete="password"
          textContentType="password"
          placeholder="••••••••"
        />

        {error ? <Text style={styles.error}>{error}</Text> : null}

        <View style={styles.actions}>
          <PrimaryButton label="Log in" onPress={onSubmit} loading={loading} />
        </View>

        <LinkButton
          label="Don't have an account? Sign up"
          onPress={() => router.push('/(auth)/signup')}
        />
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: colors.navy },
  content: { paddingHorizontal: spacing.lg, paddingBottom: spacing.xl, flexGrow: 1 },
  header: { marginBottom: spacing.xl },
  brand: { ...typography.title, color: colors.amber, fontSize: 34 },
  tagline: { ...typography.body, color: colors.textSecondary, marginTop: spacing.xs },
  title: { ...typography.heading, color: colors.textPrimary, marginBottom: spacing.lg },
  error: { color: colors.danger, marginBottom: spacing.md },
  actions: { marginTop: spacing.sm, marginBottom: spacing.md },
});

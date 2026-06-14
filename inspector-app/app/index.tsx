import { Redirect } from 'expo-router';

/**
 * Entry point. The root layout's gatekeeper handles auth redirects; this just
 * points the initial route at the schedule tab (which bounces to login if
 * unauthenticated).
 */
export default function Index() {
  return <Redirect href="/(tabs)/schedule" />;
}

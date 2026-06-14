import Constants from 'expo-constants';

/**
 * Google Maps Distance Matrix wrapper for travel-time-based clash detection.
 *
 * Degrades gracefully: returns null when no API key is configured or the call
 * fails (offline, quota, web CORS). Callers fall back to a gap heuristic.
 *
 * Note: calling Distance Matrix directly from the client exposes the key and is
 * blocked by CORS on web. For production this should move behind a Supabase
 * Edge Function; the client interface here stays the same.
 */

const extra = (Constants.expoConfig?.extra ?? {}) as {
  googleMapsApiKey?: string;
};

const API_KEY =
  process.env.EXPO_PUBLIC_GOOGLE_MAPS_API_KEY ?? extra.googleMapsApiKey ?? '';

export function hasTravelTimeProvider(): boolean {
  return API_KEY.length > 0;
}

/** Driving minutes between two addresses, or null if unavailable. */
export async function getTravelMinutes(
  origin: string,
  destination: string,
): Promise<number | null> {
  if (!API_KEY || !origin || !destination) return null;
  try {
    const url =
      'https://maps.googleapis.com/maps/api/distancematrix/json' +
      `?units=metric&mode=driving&departure_time=now` +
      `&origins=${encodeURIComponent(origin)}` +
      `&destinations=${encodeURIComponent(destination)}` +
      `&key=${API_KEY}`;
    const res = await fetch(url);
    const json = (await res.json()) as {
      rows?: { elements?: { status?: string; duration?: { value?: number }; duration_in_traffic?: { value?: number } }[] }[];
    };
    const el = json?.rows?.[0]?.elements?.[0];
    if (!el || el.status !== 'OK') return null;
    const seconds = el.duration_in_traffic?.value ?? el.duration?.value;
    return typeof seconds === 'number' ? Math.round(seconds / 60) : null;
  } catch {
    return null;
  }
}

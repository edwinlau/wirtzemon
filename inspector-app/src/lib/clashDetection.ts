import type { Inspection } from '@/types/database';
import { formatTime } from '@/lib/datetime';

/** Assumed open-home duration when an end time isn't known. */
export const DEFAULT_INSPECTION_MINUTES = 30;
/** Slack added on top of estimated drive time before we warn. */
export const TRAVEL_BUFFER_MINUTES = 10;
/** Fallback threshold when no travel-time provider is configured. */
const TIGHT_GAP_FALLBACK_MINUTES = 20;

export type ClashType = 'overlap' | 'tight_travel' | 'tight_gap';

export interface Clash {
  type: ClashType;
  message: string;
}

/** Sort inspections that have a schedule_time, earliest first. */
export function sortByStart(inspections: Inspection[]): Inspection[] {
  return [...inspections]
    .filter((i) => i.schedule_time)
    .sort(
      (a, b) =>
        new Date(a.schedule_time!).getTime() -
        new Date(b.schedule_time!).getTime(),
    );
}

function shortAddress(address: string): string {
  return address.split(',')[0].trim();
}

/**
 * Flag overlaps and tight transitions between consecutive inspections.
 * `travelByDestId` maps a destination inspection id to estimated drive minutes
 * from the inspection immediately before it (computed by the caller). The
 * resulting warning is attached to the *later* inspection in each pair.
 */
export function detectClashes(
  inspections: Inspection[],
  travelByDestId: Map<string, number>,
): Map<string, Clash> {
  const sorted = sortByStart(inspections);
  const clashes = new Map<string, Clash>();

  for (let i = 1; i < sorted.length; i++) {
    const prev = sorted[i - 1];
    const cur = sorted[i];
    const prevStart = new Date(prev.schedule_time!);
    const curStart = new Date(cur.schedule_time!);
    const prevEnd = new Date(
      prevStart.getTime() + DEFAULT_INSPECTION_MINUTES * 60_000,
    );

    if (curStart.getTime() < prevEnd.getTime()) {
      clashes.set(cur.id, {
        type: 'overlap',
        message: `Overlaps with ${shortAddress(prev.address)} (${formatTime(prevStart)})`,
      });
      continue;
    }

    const gapMin = Math.round(
      (curStart.getTime() - prevEnd.getTime()) / 60_000,
    );
    const travel = travelByDestId.get(cur.id);

    if (typeof travel === 'number') {
      if (gapMin < travel + TRAVEL_BUFFER_MINUTES) {
        clashes.set(cur.id, {
          type: 'tight_travel',
          message: `~${travel} min drive from ${shortAddress(prev.address)}, only ${gapMin} min to get there`,
        });
      }
    } else if (
      prev.address !== cur.address &&
      gapMin < TIGHT_GAP_FALLBACK_MINUTES
    ) {
      clashes.set(cur.id, {
        type: 'tight_gap',
        message: `Only ${gapMin} min after ${shortAddress(prev.address)} — check travel time`,
      });
    }
  }

  return clashes;
}

/** Consecutive same-day pairs needing a travel-time lookup. */
export function travelPairs(
  inspections: Inspection[],
): { originId: string; origin: string; destId: string; destination: string }[] {
  const sorted = sortByStart(inspections);
  const pairs = [];
  for (let i = 1; i < sorted.length; i++) {
    const prev = sorted[i - 1];
    const cur = sorted[i];
    const sameDay =
      new Date(prev.schedule_time!).toDateString() ===
      new Date(cur.schedule_time!).toDateString();
    if (sameDay && prev.address !== cur.address) {
      pairs.push({
        originId: prev.id,
        origin: prev.address,
        destId: cur.id,
        destination: cur.address,
      });
    }
  }
  return pairs;
}

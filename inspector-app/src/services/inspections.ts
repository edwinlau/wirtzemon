import { supabase } from '@/lib/supabase';
import type { Inspection } from '@/types/database';
import type { ParsedEvent } from '@/lib/ics';

/** All inspections for the signed-in user, earliest schedule first. */
export async function listInspections(): Promise<Inspection[]> {
  const { data, error } = await supabase
    .from('inspections')
    .select('*')
    .order('schedule_time', { ascending: true, nullsFirst: false });
  if (error) throw error;
  return data ?? [];
}

/** A signature used to skip importing duplicates already on the schedule. */
function signature(address: string, scheduleIso: string | null): string {
  return `${address.trim().toLowerCase()}|${scheduleIso ?? ''}`;
}

export interface ImportResult {
  inserted: number;
  skipped: number;
}

/**
 * Insert parsed .ics events as inspections, skipping any that duplicate an
 * existing one (same address + start time).
 */
export async function importEvents(
  userId: string,
  events: ParsedEvent[],
  existing: Inspection[],
): Promise<ImportResult> {
  const seen = new Set(
    existing.map((i) => signature(i.address, i.schedule_time)),
  );

  const rows: {
    user_id: string;
    address: string;
    schedule_time: string;
    listing_url: string | null;
    status: 'upcoming';
  }[] = [];
  let skipped = 0;
  for (const ev of events) {
    const iso = ev.start.toISOString();
    const sig = signature(ev.address, iso);
    if (seen.has(sig)) {
      skipped += 1;
      continue;
    }
    seen.add(sig);
    rows.push({
      user_id: userId,
      address: ev.address,
      schedule_time: iso,
      listing_url: ev.listingUrl ?? null,
      status: 'upcoming' as const,
    });
  }

  if (rows.length > 0) {
    const { error } = await supabase.from('inspections').insert(rows);
    if (error) throw error;
  }

  return { inserted: rows.length, skipped };
}

export async function deleteInspection(id: string): Promise<void> {
  const { error } = await supabase.from('inspections').delete().eq('id', id);
  if (error) throw error;
}

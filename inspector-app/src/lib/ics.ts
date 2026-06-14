/**
 * Minimal, dependency-free iCalendar (.ics) parser tailored to REA/Domain
 * open-home invites. Extracts: address (LOCATION), date/time (DTSTART) and a
 * listing URL (URL property, or the first real-estate link in the body).
 *
 * Timezone note: DTSTART values ending in `Z` are parsed as UTC. Values with a
 * TZID parameter or no zone are interpreted as device-local wall-clock time —
 * which matches what a user expects for an open home in their own city. Full
 * IANA TZID conversion is intentionally out of scope (no tz library).
 */

export interface ParsedEvent {
  uid?: string;
  address: string;
  summary?: string;
  start: Date;
  end?: Date;
  listingUrl?: string;
}

function unescapeText(value: string): string {
  return value
    .replace(/\\n/gi, '\n')
    .replace(/\\,/g, ',')
    .replace(/\\;/g, ';')
    .replace(/\\\\/g, '\\')
    .trim();
}

function parseIcsDate(value: string): Date | null {
  const m = value
    .trim()
    .match(/^(\d{4})(\d{2})(\d{2})(?:T(\d{2})(\d{2})(\d{2}))?(Z)?$/);
  if (!m) return null;
  const [, y, mo, d, hh = '0', mm = '0', ss = '0', z] = m;
  const yi = +y, moi = +mo - 1, di = +d, hi = +hh, mi = +mm, si = +ss;
  const date = z
    ? new Date(Date.UTC(yi, moi, di, hi, mi, si))
    : new Date(yi, moi, di, hi, mi, si);
  return isNaN(date.getTime()) ? null : date;
}

const URL_RE = /https?:\/\/[^\s<>"')]+/gi;

function extractListingUrl(...sources: (string | undefined)[]): string | undefined {
  const urls: string[] = [];
  for (const s of sources) {
    if (!s) continue;
    const matches = s.match(URL_RE);
    if (matches) urls.push(...matches);
  }
  if (urls.length === 0) return undefined;
  // Prefer a known portal link if present.
  const portal = urls.find((u) => /realestate\.com|domain\.com/i.test(u));
  return (portal ?? urls[0]).replace(/[.,;]+$/, '');
}

interface RawEvent {
  uid?: string;
  summary?: string;
  location?: string;
  description?: string;
  url?: string;
  dtstart?: string;
  dtend?: string;
}

export function parseIcs(content: string): ParsedEvent[] {
  // Normalise newlines and unfold continuation lines (RFC 5545 line folding).
  const unfolded = content.replace(/\r\n/g, '\n').replace(/\n[ \t]/g, '');
  const lines = unfolded.split('\n');

  const events: ParsedEvent[] = [];
  let cur: RawEvent | null = null;

  for (const line of lines) {
    const trimmed = line.trim();
    if (trimmed === 'BEGIN:VEVENT') {
      cur = {};
      continue;
    }
    if (trimmed === 'END:VEVENT') {
      if (cur) {
        const start = cur.dtstart ? parseIcsDate(cur.dtstart) : null;
        if (start) {
          const address = cur.location
            ? unescapeText(cur.location)
            : cur.summary
            ? unescapeText(cur.summary)
            : 'Unknown address';
          events.push({
            uid: cur.uid,
            address,
            summary: cur.summary ? unescapeText(cur.summary) : undefined,
            start,
            end: cur.dtend ? parseIcsDate(cur.dtend) ?? undefined : undefined,
            listingUrl: extractListingUrl(cur.url, cur.description, cur.summary),
          });
        }
      }
      cur = null;
      continue;
    }
    if (!cur) continue;

    const colon = line.indexOf(':');
    if (colon === -1) continue;
    const namePart = line.slice(0, colon);
    const value = line.slice(colon + 1);
    const name = namePart.split(';')[0].toUpperCase();

    switch (name) {
      case 'UID': cur.uid = value.trim(); break;
      case 'SUMMARY': cur.summary = value; break;
      case 'LOCATION': cur.location = value; break;
      case 'DESCRIPTION': cur.description = value; break;
      case 'URL': cur.url = value.trim(); break;
      case 'DTSTART': cur.dtstart = value; break;
      case 'DTEND': cur.dtend = value; break;
      default: break;
    }
  }

  return events.sort((a, b) => a.start.getTime() - b.start.getTime());
}

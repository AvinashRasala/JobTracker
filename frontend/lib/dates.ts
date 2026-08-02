/**
 * The backend serializes datetimes as naive ISO strings with no timezone
 * marker (e.g. "2026-08-02T05:33:51.125367") -- they're always UTC
 * underneath (Python's datetime.utcnow()), but a string like that has no
 * 'Z' or '+00:00' suffix. Per the JS spec, `new Date(...)` on a date-time
 * string WITHOUT a timezone offset is parsed as LOCAL time, not UTC. That
 * silently shifts every displayed timestamp by the viewer's UTC offset
 * (e.g. ~5.5 hours off for IST). These helpers fix that by normalizing to
 * UTC before parsing -- use them instead of calling `new Date(...)`
 * directly on any date string that came from the API.
 */

const HAS_TIMEZONE = /[zZ]|[+-]\d{2}:?\d{2}$/;

export function parseApiDate(value: string | null | undefined): Date | null {
  if (!value) return null;
  const normalized = HAS_TIMEZONE.test(value) ? value : `${value}Z`;
  const date = new Date(normalized);
  return isNaN(date.getTime()) ? null : date;
}

export function formatDateTime(value: string | null | undefined): string {
  const date = parseApiDate(value);
  return date ? date.toLocaleString() : "—";
}

export function formatDate(value: string | null | undefined): string {
  const date = parseApiDate(value);
  return date ? date.toLocaleDateString() : "—";
}

/** YYYY-MM-DD, for compact display in ledger rows etc. */
export function formatDateShort(value: string | null | undefined): string {
  const date = parseApiDate(value);
  if (!date) return "—";
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

export function isPastOrNow(value: string | null | undefined): boolean {
  const date = parseApiDate(value);
  return date ? date <= new Date() : false;
}

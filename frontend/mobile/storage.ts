import AsyncStorage from '@react-native-async-storage/async-storage';

export type Message = {
  id: string;
  text: string;
  sender: 'user' | 'paparazzo';
};

// --- KEY HELPERS ---
const KEY_WEEK_START_DATE = 'diary:week_start_date';   // ISO date 'YYYY-MM-DD' of Day 1
const KEY_LAST_SESSION_DATE = 'diary:last_session_date'; // ISO date of the last day the user journaled
const KEY_MESSAGES_PREFIX = 'diary:messages:';           // followed by ISO date

/** Returns today's date in 'YYYY-MM-DD' format using the device's local timezone. */
export function todayIso(): string {
  const d = new Date();
  const yyyy = d.getFullYear();
  const mm = String(d.getMonth() + 1).padStart(2, '0');
  const dd = String(d.getDate()).padStart(2, '0');
  return `${yyyy}-${mm}-${dd}`;
}

/** Computes which day-of-the-week (1-7) a given ISO date is, given the week start. */
export function dayNumberFor(isoDate: string, weekStartIso: string): number {
  const d = new Date(isoDate + 'T00:00:00');
  const start = new Date(weekStartIso + 'T00:00:00');
  const diffMs = d.getTime() - start.getTime();
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
  return diffDays + 1; // Day 1 = first day, Day 7 = seventh day
}

// --- WEEK-START ---
export async function getWeekStartDate(): Promise<string | null> {
  return AsyncStorage.getItem(KEY_WEEK_START_DATE);
}

export async function setWeekStartDate(isoDate: string): Promise<void> {
  await AsyncStorage.setItem(KEY_WEEK_START_DATE, isoDate);
}

// --- LAST-SESSION-DATE ---
export async function getLastSessionDate(): Promise<string | null> {
  return AsyncStorage.getItem(KEY_LAST_SESSION_DATE);
}

export async function setLastSessionDate(isoDate: string): Promise<void> {
  await AsyncStorage.setItem(KEY_LAST_SESSION_DATE, isoDate);
}

// --- MESSAGES (per-day) ---
export async function getMessagesForDate(isoDate: string): Promise<Message[]> {
  const v = await AsyncStorage.getItem(KEY_MESSAGES_PREFIX + isoDate);
  return v ? JSON.parse(v) : [];
}

export async function setMessagesForDate(isoDate: string, messages: Message[]): Promise<void> {
  await AsyncStorage.setItem(KEY_MESSAGES_PREFIX + isoDate, JSON.stringify(messages));
}

/** Lists all dates that have stored messages, in chronological order. */
export async function listJournaledDates(): Promise<string[]> {
  const allKeys = await AsyncStorage.getAllKeys();
  return allKeys
    .filter((k) => k.startsWith(KEY_MESSAGES_PREFIX))
    .map((k) => k.replace(KEY_MESSAGES_PREFIX, ''))
    .sort();
}

// --- CONVENIENCE: SESSION-AWARE TODAY ---
/**
 * Returns the date the active session belongs to. If the user is currently
 * mid-session (lastSessionDate exists and we're calling this before any
 * archive), this returns lastSessionDate. Otherwise it returns today.
 *
 * The session-stickiness rule: if you started chatting at 11:58 PM yesterday
 * and your phone is still open at 12:01 AM, you're still on yesterday's session.
 * The session only ends when the app is opened *fresh* on a new calendar date.
 */
export async function getActiveSessionDate(): Promise<string> {
  const last = await getLastSessionDate();
  const today = todayIso();
  // If there's no last-session, this is a brand new session today.
  if (!last) return today;
  // If today's calendar date matches the last session, continue it.
  if (last === today) return today;
  // Otherwise, today is a fresh date and the previous session is closed.
  return today;
}

// --- DEMO RESET ---
export async function clearAll(): Promise<void> {
  const allKeys = await AsyncStorage.getAllKeys();
  const toRemove = allKeys.filter(
    (k) => k.startsWith('diary:') // catches messages, week-start, last-session, anything else
  );
  if (toRemove.length > 0) {
    await AsyncStorage.multiRemove(toRemove);
  }
}
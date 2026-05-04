// frontend/mobile/types.ts

/** A single chat message in a daily interview session. */
export type Message = {
  id: string;
  text: string;
  sender: 'user' | 'paparazzo';
};

/** The current day in the user's week. 1-indexed. */
export type DayNumber = 1 | 2 | 3 | 4 | 5 | 6 | 7;

/**
 * One day's full interview transcript, formatted for the summarizer.
 * Format: "Snap: ...\nStar: ...\nSnap: ...\nStar: ..."
 * This is the format the research/prompts.py expects.
 */
export type DayTranscript = string;

/**
 * The neutral, structured dossier maintained across the week.
 * In the decoupled pipeline this is plain text under six fixed headers
 * (PEOPLE / PLACES / EVENTS / FEELINGS / DECISIONS / QUOTES), each item
 * tagged with [Day N]. We store it as a single string because the
 * summarizer reads and writes it as text — there is no benefit to
 * parsing it into a structured object on the client side.
 */
export type Dossier = string;

/** The final stylized weekly feature article, rendered once on Day 7. */
export type Magazine = string;

/**
 * The complete state of a user's week. Persisted in AsyncStorage by
 * Medhini's storage.ts.
 */
export type WeekState = {
  weekStartIso: string;          // ISO date when Day 1 started
  currentDay: DayNumber;          // which day we are on now
  transcripts: Partial<Record<DayNumber, DayTranscript>>;  // completed days
  dossier: Dossier;               // running structured state, "" on Day 1
  magazine: Magazine | null;      // null until Day 7 generation runs
};

/**
 * Convert an array of chat Messages into the "Snap: ...\nStar: ..." 
 * transcript format the summarizer prompts expect.
 *
 * The research prompts use "Snap" for the interviewer and "Star" for the
 * user (the celebrity being interviewed). Match that exactly — the LLM
 * was prompted with these names.
 */
export function messagesToTranscript(messages: Message[]): DayTranscript {
  return messages
    .map((m) => `${m.sender === 'paparazzo' ? 'Snap' : 'Star'}: ${m.text}`)
    .join('\n');
}
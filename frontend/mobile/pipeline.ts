// frontend/mobile/pipeline.ts
//
// The decoupled summarization pipeline from the paper.
// Two stages:
//   updateDossier()   — runs at the end of each day, neutral state update
//   renderMagazine()  — runs once on Day 7, applies the Paparazzo voice
//
// The persona is applied exactly once per week, on the magazine render.

import { callLLM } from './openaiClient';
import {
  DECOUPLED_STATE_UPDATE_PROMPT,
  DECOUPLED_MAGAZINE_RENDER_PROMPT,
} from './prompts';
import { Dossier, DayTranscript, DayNumber, Magazine } from './types';

/**
 * Update the running dossier with today's transcript.
 * Called at the end of each day's chat session.
 *
 * @param previousDossier  The dossier as of yesterday. Pass "" on Day 1.
 * @param todaysTranscript Today's interview, formatted as "Snap: ...\nStar: ..."
 * @param dayNumber        Which day this is (1-7). Used for sanity context.
 * @returns                The new dossier including today's facts.
 */
export async function updateDossier(
  previousDossier: Dossier,
  todaysTranscript: DayTranscript,
  dayNumber: DayNumber
): Promise<Dossier> {
  const userContent = buildStateUpdateInput(
    previousDossier,
    todaysTranscript,
    dayNumber
  );

  return await callLLM({
    systemPrompt: DECOUPLED_STATE_UPDATE_PROMPT,
    userContent,
    maxTokens: 1200,  // product-side tuning; paper's frozen config is 900.
    temperature: 0.7,
  });
}

/**
 * Render the final dossier as a stylized weekly magazine article.
 * Called once, on Day 7, after the dossier has been updated for that day.
 *
 * @param finalDossier The dossier after Day 7's update has been applied.
 * @returns            The stylized magazine article.
 */
export async function renderMagazine(finalDossier: Dossier): Promise<Magazine> {
  return await callLLM({
    systemPrompt: DECOUPLED_MAGAZINE_RENDER_PROMPT,
    userContent: `DOSSIER:\n${finalDossier}`,
    maxTokens: 1000,
    temperature: 0.7,
  });
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function buildStateUpdateInput(
  previousDossier: Dossier,
  todaysTranscript: DayTranscript,
  dayNumber: DayNumber
): string {
  const dossierBlock =
    previousDossier.trim().length === 0
      ? '(empty — this is Day 1)'
      : previousDossier;

  return [
    `CURRENT DOSSIER STATE:`,
    dossierBlock,
    ``,
    `TODAY'S INTERVIEW TRANSCRIPT (Day ${dayNumber}):`,
    todaysTranscript,
  ].join('\n');
}
// frontend/mobile/scripts/test_pipeline.ts
//
// Runs the decoupled pipeline against research/data/weeks/week_01.json
// Prints the final magazine to stdout. Use this to validate the pipeline
// works end-to-end before wiring it into the mobile UI.
//
// Run with:
//   cd frontend/mobile
//   npx ts-node scripts/test_pipeline.ts
// (or compile with tsc and run with node)

import * as fs from 'fs';
import * as path from 'path';
import { updateDossier, renderMagazine } from '../pipeline';
import { DayNumber, Dossier } from '../types';

// Path is relative to where you run from. Adjust if your repo root is elsewhere.
const WEEK_FILE = path.resolve(
  __dirname,
  '../../../research/data/weeks/week_01.json'
);

type WeekFixture = {
  week_id: number;
  persona: string;
  facts: Array<{ id: string; day: number; type: string; text: string }>;
  transcripts: Record<string, string>;
};

async function main() {
  const raw = fs.readFileSync(WEEK_FILE, 'utf-8');
  const week: WeekFixture = JSON.parse(raw);

  console.log('=== Persona ===');
  console.log(week.persona);
  console.log();

  let dossier: Dossier = '';
  for (let day = 1 as DayNumber; day <= 7; day = (day + 1) as DayNumber) {
    const transcript = week.transcripts[String(day)];
    if (!transcript) {
      throw new Error(`Missing transcript for day ${day}`);
    }
    console.log(`--- Day ${day}: updating dossier... ---`);
    dossier = await updateDossier(dossier, transcript, day);
    console.log(`(dossier length: ${dossier.length} chars)`);
  }

  console.log();
  console.log('=== Final dossier (Day 7) ===');
  console.log(dossier);
  console.log();
  console.log('--- Generating magazine... ---');
  const magazine = await renderMagazine(dossier);
  console.log();
  console.log('=== Magazine ===');
  console.log(magazine);

  // Save it for inspection
  const outPath = path.resolve(__dirname, 'test_pipeline_output.json');
  fs.writeFileSync(
    outPath,
    JSON.stringify({ persona: week.persona, dossier, magazine }, null, 2)
  );
  console.log();
  console.log(`Output saved to ${outPath}`);
}

main().catch((err) => {
  console.error('Pipeline test failed:', err);
  process.exit(1);
});
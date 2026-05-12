# Star Diary — Mobile App

A React Native journaling app where a tabloid-style AI interviewer ("Snap, the Paparazzo") collects daily statements from the user over seven days and produces a stylized weekly magazine on Day 7. Built on Expo SDK 54.

This app implements the *decoupled* summarization architecture from the research paper at the root of this repository. Every architectural choice — the daily question cap, the structured dossier, the once-per-week magazine render — traces to a specific finding in the paper.

---

## Quick start

From this directory:

```bash
npm install
```

Create a `.env` file at the root of `frontend/mobile/`:

```
EXPO_PUBLIC_OPENAI_API_KEY=sk-...
```

The `EXPO_PUBLIC_` prefix is required — Expo only exposes env vars with this prefix to the running app. Set a spending cap on the OpenAI key before bundling for any kind of demo or distribution; the key ships in the app bundle.

Then:

```bash
npx expo start
```

Scan the QR code with Expo Go on your phone (iOS: Camera app, Android: Expo Go app). Both devices must be on the same Wi-Fi network. For tunneled mode if Wi-Fi is uncooperative: `npx expo start --tunnel` (slower).

Restart with cache cleared if anything looks stale: `npx expo start --clear`.

---

## Architecture

The app has four bottom-tab screens. One is the working core of the product; three are placeholders for the upcoming roadmap.

```
App.tsx                          Bottom-tab navigator shell, font loading, gradient background
  ├── screens/InterviewScreen    The daily chat with Paparazzo (built out)
  ├── screens/CalendarScreen     Day-by-day archive of past chats (placeholder)
  ├── screens/MagazineScreen     The weekly magazine display (placeholder)
  └── screens/FeaturedScreen     Day-of-origin diagnostic view (placeholder)
```

The summarization layer is implemented as pure modules that the screens import:

```
pipeline.ts        The decoupled pipeline as two pure functions:
                     updateDossier(prevDossier, todayTranscript, dayNumber)
                     renderMagazine(finalDossier)

prompts.ts         Five prompts copied verbatim from research/prompts.py.
                   Two are used at runtime (DECOUPLED_STATE_UPDATE,
                   DECOUPLED_MAGAZINE_RENDER); the others are retained
                   for code-completeness with the paper.

openaiClient.ts    Thin wrapper around the OpenAI SDK. Reads
                   EXPO_PUBLIC_OPENAI_API_KEY. Sets
                   dangerouslyAllowBrowser: true.

storage.ts         AsyncStorage helpers, all keys prefixed 'diary:':
                     diary:messages:YYYY-MM-DD       per-day chat
                     diary:week_start_date           ISO date of Day 1
                     diary:last_session_date         session-stickiness
                     diary:dossier:<weekStartIso>    decoupled state
                     diary:magazine:<weekStartIso>   final artifact
                     diary:dossier_days_completed:<weekStartIso>

types.ts           Message, Dossier, Magazine, DayNumber. Plus
                   messagesToTranscript() — converts a chat array into
                   the "Snap: ...\nStar: ..." transcript format the
                   summarizer prompts expect.

theme.ts           Design tokens (cream/gold/deepBlack palette,
                   Playfair Display + Cedarville Cursive fonts).

components/        Reusable design-system components:
  DiaryCover         Animated diary cover with "Begin Journal" button
  DiaryPage          The handwriting-style page transition
```

### How the pieces fit together

When the user completes Day N's interview (8 questions + 1 closing remark = 9 Paparazzo replies):

1. `InterviewScreen` calls `runDailyDossierUpdate(messages)`.
2. That function reads the previous dossier from `storage.ts`, calls `updateDossier(...)` from `pipeline.ts`, writes the new dossier back to storage, and marks Day N as completed.
3. After every day's update, `runMagazineRender(dossier)` regenerates the magazine. (The paper's protocol runs this only on Day 7; the product runs it after every day so the magazine is always demo-ready. See "Departures from the paper" below.)
4. On next launch, `reconcileDossier()` retries any dossier updates that failed mid-call (e.g., network died right after the celebration screen).

The magazine string lives at `diary:magazine:<weekStartIso>` once generated. The not-yet-built `MagazineScreen` will read from that key.

---

## The Interview screen in detail

`screens/InterviewScreen.tsx` is ~1,150 lines and holds the entire daily-chat experience. Worth knowing the key mechanics:

- **8 questions + 1 closing remark.** A runtime "routing instruction" is injected as a second system message on each turn, telling the LLM whether to ask a probing question (turns 1–8) or deliver a no-question closing remark (turn 9). The frozen `PAPARAZZO_INTERVIEWER_PROMPT` is never modified at runtime.
- **Soft warning at question 6.** The routing instruction at turn 6 requires a tabloid-style time-pressure callout ("running out of column inches, superstar") before the actual question.
- **Closing remark stripped.** Even with explicit override instructions, the LLM sometimes appends a question to its closing reply. `stripTrailingQuestion()` removes any trailing question sentences from the Day 9 reply as a safety net.
- **Session stickiness across midnight.** If the user starts journaling at 11:58 PM and crosses midnight, that session still counts as the day it started on. A new session only starts when the app is reopened on a different calendar date.
- **Day-complete celebration → countdown panel.** After the closing remark, a "Day N of 7 — captured" panel appears. Tap-to-dismiss reveals a passive countdown to midnight ("9 hours until your next exclusive").
- **Lined-paper background, per-message timestamps, sticky date bar** ("Day N of 7 · 5 May") below the header.

There is also a **testing-only refresh button** in the top-right of the header that wipes today's session via an `Alert`-confirmed `clearAll()`. **This must be removed before any public release.** Search for `TODO: remove before demo` to find it.

---

## Departures from the paper

The product is built on the paper's findings but tunes a few parameters for product reasons. These are documented here so reviewers can verify nothing changed about the architecture.

- **Dossier max-tokens bumped from 900 (paper) to 1200 (product).** Real journal sessions are longer than the synthetic-corpus sessions; 900 truncated dossiers mid-string. The architectural property — decoupling neutral state propagation from a single stylistic render — is unchanged; only the capacity is tuned. Magazine render stays at 1000 tokens to match the paper.
- **Magazine regenerates after every day completion, not only on Day 7.** The paper's protocol runs the magazine render exactly once. The product regenerates it after each day so the user (and demo audience) can see a magazine at any point during the week. Each regeneration overwrites the previous. Architectural property unchanged.
- **Frontend-only architecture.** The OpenAI SDK runs directly in the app with `dangerouslyAllowBrowser: true`. There is no server. An earlier version proxied through a FastAPI backend (`../../backend/`); that backend is retained for historical reference but is not used.

The five prompts in `prompts.ts` are **verbatim copies** of the frozen research prompts in `../../research/prompts.py`. Do not modify them. Any change invalidates consistency with the paper.

---

## Testing the pipeline

`scripts/test_pipeline.ts` runs the decoupled pipeline end-to-end against the synthetic Week 1 corpus from `../../research/data/weeks/week_01.json`. Use it to validate any pipeline change before touching the mobile UI.

```bash
EXPO_PUBLIC_OPENAI_API_KEY=sk-... \
  npx ts-node --compiler-options '{"module":"CommonJS"}' \
  scripts/test_pipeline.ts
```

The `--compiler-options` flag is needed because `ts-node` defaults to ES-module resolution under recent Node versions; the test script uses CommonJS-style imports.

Expected output: 7 dossier-update calls (one per day), the final dossier text, then the magazine. Total runtime: ~1–3 minutes. Cost: ~$0.05 per run on `gpt-4o-mini`.

Output is saved to `scripts/test_pipeline_output.json` for inspection. A reference baseline from an earlier validated run is checked in.

---

## Known issues and gotchas

- **Expo SDK 54 + React 19 is recent.** Expo Go must be up to date. If you see "this project uses SDK X but Expo Go supports up to Y," update Expo Go from the app store.
- **The four screens have different completion states.** `InterviewScreen` is the working core. `CalendarScreen`, `MagazineScreen`, and `FeaturedScreen` are intentional placeholders for the next development iteration — they render a coming-soon panel but do not yet read from storage or display content. The summarization layer they will consume *is* fully wired and populating storage correctly; only the display UIs remain.
- **The testing refresh button is destructive.** It wipes all `diary:*` storage keys. The `Alert` confirmation is the only guard. Remove this button before any public release. See "TODO: remove before demo" comments.
- **OpenAI calls fail silently in the dossier update.** By design — the user just finished journaling and is looking at the celebration screen; we don't want to break that moment with an error. Failures log to the Metro console; the next app launch reconciles any missing updates via `reconcileDossier()`.
- **`@react-native-async-storage/async-storage` is a native module.** Install it with `npx expo install`, not plain `npm install`, so Expo can manage the native binding versioning.
- **API key in the bundle.** The `EXPO_PUBLIC_OPENAI_API_KEY` is embedded in the compiled app. This is fine for demos on your own devices; for any wider distribution, this needs to move to a server proxy with proper key management.

---

## What's in `assets/`

App icons (Android adaptive icon background/foreground/monochrome, iOS icon, web favicon, splash screen). Replace these if forking. No other static assets are bundled; fonts are loaded from `@expo-google-fonts` at runtime.

---

## Where to go next

- For the research backing the architecture: `../../research/RESEARCH_README.md`
- For the root-level project overview: `../../README.md`
- For the published paper: see citation in the root README

---

**Team MARS** — Akshat Daruka · Medhini Oak · Ritwika Sen
Otto von Guericke University Magdeburg
# Star Diary

A journaling app where a tabloid-style AI interviewer ("Snap, the Paparazzo") collects daily statements from the user and, at the end of seven days, publishes a stylized weekly magazine. The product is the testbed for a research paper on a fragility we discovered in the natural way to build it.

This repository contains both the **product** (a working React Native / Expo mobile app) and the **research** (15-week synthetic corpus, three-pipeline study, statistical analysis, paper-ready figures, and a real-world generalization probe).

---

## Two halves, one project

**Product — Star Diary.** A mobile journaling app built on the architectural finding of our paper. Star Diary uses the *decoupled* pipeline: it maintains a neutral, structured dossier across the week and applies the stylistic persona exactly once, at the end-of-week magazine render. The product is research-grounded by design — every architectural choice traces to a result in the paper.

**Research — "When the Voice Erases the Memory."** We compare three architectures (neutral, stylized, decoupled) on a controlled 15-week synthetic corpus of 327 pre-registered facts, evaluate fact preservation against the ground-truth list using a two-judge LLM evaluation protocol validated against three human reviewers, and report a day-of-origin diagnostic that surfaces compounding fact loss invisible to standard summarization metrics. The findings replicate across two models and on out-of-distribution real-world data (Greenland sovereignty interviews).

The headline finding: a recursive summarizer with a strong persona baked in preserves only **26.3 %** of facts across a week. The decoupled architecture restores this to **85.6 % – 96.3 %** depending on the model — and eliminates the day-of-origin decay gradient entirely.

---

## Where to go from here

### 🎙️ For the product — `frontend/mobile/`

The Star Diary mobile app. React Native + Expo, runs on iOS and Android via Expo Go.

- **`frontend/mobile/App.tsx`** — Navigation shell (bottom-tab navigator with four screens: Interview, Calendar, The Magazine, Featured).
- **`frontend/mobile/screens/InterviewScreen.tsx`** — The daily chat with the Paparazzo persona. Implements the 8-question cap, the closing remark, the day-complete celebration, and the next-day countdown.
- **`frontend/mobile/pipeline.ts`** — The decoupled summarization pipeline as a pure module. Two functions: `updateDossier(prevDossier, todayTranscript, dayNumber)` and `renderMagazine(finalDossier)`. The prompts in `prompts.ts` are copied verbatim from the frozen research prompts.
- **`frontend/mobile/storage.ts`** — Per-day AsyncStorage with `messages:YYYY-MM-DD` keys, plus week-scoped dossier and magazine storage.
- **`frontend/mobile/scripts/test_pipeline.ts`** — End-to-end pipeline validation against the synthetic Week 1 corpus.

To run the app locally: `cd frontend/mobile && npm install && npx expo start`, then scan the QR code with Expo Go. Set `EXPO_PUBLIC_OPENAI_API_KEY` in a `.env` file in `frontend/mobile/`.

### 📊 For the research — `research/`

The controlled study and everything around it. Start at **`research/RESEARCH_README.md`** for the full walkthrough — pipelines, methodology, headline results, repository layout, reproduction instructions, data schemas, and known limitations.

What you'll find inside:

- **`research/prompts.py`** — The five frozen prompts (interviewer, neutral summarizer, stylized summarizer, decoupled state updater, decoupled magazine renderer).
- **`research/pipelines.py`** — The three pipeline implementations.
- **`research/synthetic_weeks.py`** — Week and transcript generator for the 15-persona corpus.
- **`research/judge.py`** — Two-judge LLM evaluator (strict + lenient).
- **`research/data/weeks/`** — The 15 pre-registered weeks (`week_01.json` … `week_15.json`), 327 facts total.
- **`research/data/results/`** — Pipeline outputs across primary (`openai-4o-mini`) and cross-model (`openai-4.1-mini`) runs.
- **`research/data/judgments/`** — Per-fact judge verdicts and human spot-check data.
- **`research/data/greenland/`** — The out-of-distribution generalization probe: 7 verbatim political interviews on the Greenland sovereignty crisis (Dec 2024 – Jan 2026), 27 LLM-extracted facts, all three pipelines applied.
- **`research/figures/`** and **`research/figures_gpt41mini/`** — Paper-ready PNGs and statistical CSVs.
- **`research/stats_analysis.py`**, **`research/analyze.py`**, **`research/metrics_auto.py`** — Statistical analysis, decay-curve figure generator, aggregate metrics (ROUGE/BERTScore/G-Eval).

### 📝 For raw logs — `logs/`

`logs/llm_calls.jsonl` — A per-call audit log capturing every LLM API call during research runs: model identifier, prompt hash (SHA-256), temperature, max-tokens, latency, token usage. Used for reproducibility verification.


**Team MARS** — Akshat Daruka · Medhini Oak · Ritwika Sen
Otto von Guericke University Magdeburg, May 2026

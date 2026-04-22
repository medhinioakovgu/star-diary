## Project Overview

This repository contains the code and data for our 12-page ACM-format research paper: **"Does Recursive Stylized Summarization Cause Fact Loss? A Day-of-Origin Diagnostic for AI Journaling Agents."**

We built **Star-Interview Diary**, a journaling application where an AI "Paparazzo" interviews a user daily and, at the end of the week, produces a weekly magazine summary of their life. The app runs three different summarization pipelines and we measure whether stylistic persona pressure causes facts from early in the week to be systematically lost by the final Day-7 summary.

### The Core Hypothesis

When a weekly magazine is produced by _recursively_ summarizing daily summaries — each step applying a heavy tabloid "Paparazzo" voice — facts from early days get compressed, paraphrased, and eventually dropped. Facts introduced on Day 1 pass through 6 rounds of stylized summarization before appearing in the final magazine; facts from Day 7 pass through none. We call this **compounding fact decay** and measure it with a **day-of-origin diagnostic**: for each tagged fact, we track which day it was introduced and whether it survived to the final magazine.

---

## Research Questions

**RQ1:** Does stylistic pressure amplify fact loss in recursive summarization, and does the loss compound across recursion steps?

**RQ2:** Does decoupling factual state from stylistic rendering preserve faithfulness without sacrificing stylistic adherence?

**RQ3:** Do aggregate automatic metrics (ROUGE, BERTScore, G-Eval) capture the compounding fact decay, or does it require a day-of-origin diagnostic?

---

## The Three Pipelines

| Pipeline      | Description                                                                                                                                                                            |
| ------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **neutral**   | Recursive daily summarization with no persona. Each day's summary is built from the previous day's summary + today's transcript. Factual baseline.                                     |
| **stylized**  | Identical to neutral but the Paparazzo persona voice is applied at every recursive step. This is the condition under test for RQ1.                                                     |
| **decoupled** | Factual state is propagated neutrally each day. A single one-shot Paparazzo render is applied only at the final step to produce the magazine. Designed to fix RQ1 while answering RQ2. |

---

## Key Results

| Pipeline  | Fact preservation (strict judge) | ROUGE-1 | BERTScore-F |
| --------- | -------------------------------- | ------- | ----------- |
| neutral   | **95.6%**                        | 0.323   | 0.777       |
| stylized  | **24.5%**                        | 0.171   | 0.739       |
| decoupled | **83.5%**                        | 0.353   | 0.780       |

Inter-judge agreement: κ = 0.892 (near-perfect). BERTScore varies by only 0.04 despite a 71-point judge gap, confirming RQ3.

---

## Repository Structure

```
star-diary/
│
├── README.md                        ← this file
│
├── backend/                         ← product app backend (FastAPI)
│   └── ...
│
├── frontend/                        ← web frontend (React)
│   └── ...
│
├── frontend/mobile/                 ← mobile frontend
│   └── ...
│
└── research/                        ← RESEARCH PIPELINE (all paper code is here)
    │
    ├── RESEARCH_README.md           ← research pipeline overview (start here)
    ├── EVALUATION_README.md         ← evaluation pipeline documentation
    │
    ├── prompts.py                   ← FROZEN. All LLM prompts. Do not edit.
    ├── llm_client.py                ← FROZEN. Unified API wrapper (OpenAI + Groq).
    ├── synthetic_weeks.py           ← Generates 15 synthetic user personas + week data
    ├── pipelines.py                 ← Runs neutral / stylized / decoupled pipelines
    ├── judge.py                     ← LLM-as-judge harness (strict + lenient)
    ├── analyze.py                   ← Produces figures and tables from judgments
    ├── metrics_auto.py              ← ROUGE, BERTScore, G-Eval (RQ3)
    ├── spot_check.py                ← Streamlit human validation UI
    ├── fix_neutral_truncation.py    ← One-shot fix for neutral max_tokens bug
    │
    ├── data/
    │   ├── weeks/                   ← week_01.json … week_15.json (input data)
    │   ├── results/                 ← pipeline outputs (one folder per week/model)
    │   └── judgments/               ← judge CSVs, automatic metrics, human spotcheck
    │
    ├── figures/
    │   ├── README.md                ← captions, LaTeX paths, numbers for the paper
    │   ├── fig1_decay_strict.png    ← HEADLINE FIGURE
    │   ├── fig1_decay_lenient.png   ← robustness check (appendix)
    │   ├── fig2_decay_by_type_strict.png
    │   ├── summary_table.csv        ← Table 1 in paper
    │   └── interjudge_agreement.txt ← κ = 0.892
    │
    └── logs/
        └── llm_calls.jsonl          ← every API call logged (for reproducibility)
```

---

## How to Reproduce the Results

### Prerequisites

- Python 3.9+
- API keys in `research/.env`:
  ```
  OPENAI_API_KEY=sk-...
  GROQ_API_KEY=gsk_...
  ```
- Install dependencies:
  ```bash
  cd research/
  pip install -r requirements.txt
  pip install rouge-score bert-score streamlit
  ```

### Step 1 — Generate synthetic weeks (already done; skip if data/weeks/ exists)

```bash
cd research/
python synthetic_weeks.py
```

Produces 15 synthetic user personas with 7-day interview transcripts and tagged facts. Output: `data/weeks/week_01.json` … `week_15.json`.

### Step 2 — Run the three pipelines (already done; skip if data/results/ exists)

```bash
python pipelines.py --pipelines neutral stylized decoupled --model openai-4o-mini
```

Runs all three pipelines for all 15 weeks. Output: `data/results/week_XX/openai-4o-mini/{neutral,stylized,decoupled}.json`.

### Step 3 — Run the LLM judge

```bash
python judge.py --artifact weekly_magazine --judge_model openai-4o-mini
```

Judges every (week, pipeline, fact) triple with two judge strictness levels. Output: `data/judgments/judgments_weekly_magazine_openai-4o-mini.csv` (1,833 rows).

### Step 4 — Produce figures

```bash
python analyze.py --judgments data/judgments/judgments_weekly_magazine_openai-4o-mini.csv
```

Output: all files in `figures/`.

### Step 5 — Compute automatic metrics

```bash
python metrics_auto.py --geval
```

Output: `data/judgments/automatic_metrics.csv`.

### Step 6 — Human spot-check (optional, for validation)

```bash
streamlit run spot_check.py
```

Each reviewer enters their name, rates 17 items, and the app computes human–LLM agreement on completion. Output: `data/judgments/human_spotcheck.csv`.

---

## Data Schema

### Week file (`data/weeks/week_XX.json`)

```json
{
  "week_id": 1,
  "persona": "A 35-year-old physiotherapist in Oslo...",
  "facts": [
    {"id": "f01", "day": 1, "type": "quantitative", "text": "ran 10 kilometers on Monday"}
  ],
  "facts_by_day": {"1": [...], "2": [...], ..., "7": [...]},
  "transcripts": {"1": "Snap: ...\nStar: ...", ..., "7": "..."}
}
```

Fact types: `named_entity`, `quantitative`, `relational`, `emotional`.

### Pipeline result file (`data/results/week_XX/<model>/<pipeline>.json`)

```json
{
  "pipeline": "neutral",
  "model": "openai-4o-mini",
  "daily_summaries": {"1": "...", ..., "7": "..."},
  "weekly_magazine": "..."
}
```

### Judgment CSV (`data/judgments/judgments_weekly_magazine_openai-4o-mini.csv`)

One row per `(week_id, pipeline, gen_model, fact_id)`.  
Key columns: `fact_day`, `fact_type`, `verdict_strict`, `verdict_lenient`, `evidence_strict`, `evidence_lenient`.

---

## Known Limitations

- All 15 weeks were generated with `openai-4o-mini`. Cross-model robustness (Groq Llama) covers Week 1 only (archived in `data/results_groq_archived/`).
- The LLM judge runs at temperature=0.0 (deterministic for a given model snapshot). Model version dates are logged in `logs/llm_calls.jsonl`.
- Synthetic personas do not represent real users. Findings characterize model behavior under controlled conditions.

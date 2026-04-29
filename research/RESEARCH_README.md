# Star-Diary Research

This directory contains the code, data, and figures for the paper **"When the Voice Erases the Memory: Compounding Fact Decay in Recursive Stylized Diary Summarization"** (Daruka, Oak, & Sen, Otto von Guericke University Magdeburg).

The paper studies whether recursive summarization with a strong stylistic persona causes compounding, day-of-origin-dependent fact loss across a week, and whether decoupling neutral state propagation from a single end-of-week stylistic render eliminates the loss.

> The product (a journaling app called Star Diary, in `../backend/` and `../frontend/`) is the testbed. Everything in `research/` is the controlled study.

---

## Research questions

- **RQ1.** Does stylistic pressure on a recursive summarizer cause compounding, day-of-origin-dependent fact loss across a week?
- **RQ2.** Does decoupling neutral structured-state propagation from a single end-of-week stylistic render eliminate that gradient?
- **RQ3.** Do standard aggregate summarization metrics detect the magnitude of the gap, or only its direction?

---

## The three pipelines

| Pipeline      | Persona applications | Daily state                              | Day-7 magazine source           |
| ------------- | :------------------: | ---------------------------------------- | ------------------------------- |
| **Neutral**   | 0                    | Free-prose neutral summary, recursive    | Day-7 summary itself            |
| **Stylized**  | 7                    | Free-prose Paparazzo-voice dossier, recursive | Day-7 dossier itself       |
| **Decoupled** | 1                    | Neutral structured dossier under six fixed headers (`PEOPLE / PLACES / EVENTS / FEELINGS / DECISIONS / QUOTES`), each item day-tagged | Single Paparazzo render of Day-7 dossier |

The variable that separates them is **how many times stylistic pressure is applied** during the week (0, 7, or 1) — not whether the final output is stylistic.

---

## Headline results

Fact-preservation rates (lenient judge primary, strict judge in brackets), 15 weeks × 3 pipelines × 327 pre-registered facts = 981 judgments per generation model.

| Generation model | Pipeline   | Preservation (strict)        | Preservation (lenient)       |
| ---------------- | ---------- | ---------------------------- | ---------------------------- |
| `gpt-4o-mini`    | Neutral    | **96.3%** [93.3, 98.8]       | 97.3% [94.2, 99.7]           |
| `gpt-4o-mini`    | Stylized   | **24.2%** [19.6, 30.3]       | 26.5% [19.8, 35.0]           |
| `gpt-4o-mini`    | Decoupled  | **82.9%** [78.4, 87.3]       | 85.6% [81.8, 89.4]           |
| `gpt-4.1-mini`   | Neutral    | 72.6% [63.8, 80.4]           | 84.8% [74.8, 92.4]           |
| `gpt-4.1-mini`   | Stylized   | 20.8% [16.6, 26.7]           | 28.1% [21.9, 35.0]           |
| `gpt-4.1-mini`   | Decoupled  | **93.2%** [89.3, 96.6]       | 96.3% [92.6, 99.3]           |

CIs are 95% bootstrap percentile, 10,000 resamples at the week level.

**Inter-judge agreement** (strict vs lenient, 981 judgments): Cohen's κ = 0.898 (near-perfect).
**Human–LLM agreement** (3-reviewer × 17 items): 94.1% (κ = 0.850) for the lenient judge; 82.4% (κ = 0.549) for the strict judge.

Day-of-origin curves and aggregate-metric comparisons are in `figures/`. See the paper for full statistical analysis (paired Wilcoxon, all p < 0.013).

---

## Repository layout

```
research/
├── README.md                          this file
│
├── prompts.py                         FROZEN. The five canonical prompts.
├── pipelines.py                       FROZEN. Neutral / stylized / decoupled pipelines.
├── synthetic_weeks.py                 FROZEN. Week + transcript generator.
├── judge.py                           FROZEN. Two-judge harness (strict + lenient).
├── llm_client.py                      Unified API wrapper (OpenAI; Groq path retained, unused).
│
├── analyze.py                         Builds figures from a judgments CSV.
├── stats_analysis.py                  Bootstrap CIs + paired Wilcoxon tests.
├── metrics_auto.py                    ROUGE, BERTScore, G-Eval (RQ3).
├── ablation_budget.py                 Token-budget ablation (Section 4.5 of paper).
├── cross_model_table.py               Combines per-model summaries into one CSV.
├── add_cis_to_cross_model_table.py    Augments cross-model table with bootstrap CIs.
├── build_combined_figure.py           Side-by-side primary + cross-model figure.
├── polish_figures.py                  Final styling pass for paper-ready figures.
├── dedup_judgments.py                 One-shot utility: removed duplicate judge rows.
├── fix_neutral_truncation.py          One-shot utility: re-ran one truncated week.
├── fix_neutral_truncation_4_1mini.py  Same fix on the cross-model run.
├── spot_check.py                      Streamlit UI for human validation (3-reviewer).
├── analyze_spotcheck.py               Computes human–LLM and inter-rater κ.
│
├── data/
│   ├── weeks/                         15 pre-registered weeks (week_01.json … week_15.json)
│   ├── results/week_XX/openai-4o-mini/{neutral,stylized,decoupled}.json
│   ├── results/week_XX/openai-4.1-mini/{neutral,stylized,decoupled}.json
│   ├── results/week_XX/openai-4o-mini/stylized_1000tok.json   (5 weeks: budget ablation)
│   └── judgments/
│       ├── judgments_weekly_magazine_openai-4o-mini.csv       primary, 981 rows
│       ├── gpt41mini/judgments_weekly_magazine_openai-4o-mini.csv  cross-model, 981 rows
│       ├── ablation/judgments_weekly_magazine_openai-4o-mini.csv   budget ablation, 110 rows
│       ├── automatic_metrics.csv                              ROUGE/BERTScore/G-Eval, 90 rows
│       └── human_spotcheck.csv                                3 reviewers × 17 items
│
├── figures/                           paper-ready PNGs + statistical CSVs (primary model)
└── figures_gpt41mini/                 same, cross-model
```

`prompts.py`, `pipelines.py`, `synthetic_weeks.py`, and `judge.py` were frozen at the start of data collection. Modifying them invalidates the corpus and requires full regeneration.

---

## Reproducing the results

### Prerequisites

Python 3.9+. From the repo root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install rouge-score bert-score streamlit  # only needed for metrics_auto / spot_check
```

Create `.env` at the repo root with:

```
OPENAI_API_KEY=sk-...
```

### Step 1 — Generate the synthetic corpus

```bash
cd research
python synthetic_weeks.py --count 15 --model openai-4o-mini
```

Already populated. Output: `data/weeks/week_01.json` … `week_15.json`. Each file contains the persona, the pre-registered fact list (with `day` and `type` tags), the per-day fact assignments, and the seven daily Snap↔Star transcripts. Generation seed: `random.seed(42)`. Week 8 was regenerated once (the only deviation from one-shot generation; first run over-delivered facts).

### Step 2 — Run the three pipelines

```bash
# Primary model
python pipelines.py --model openai-4o-mini

# Cross-model robustness
python pipelines.py --model openai-4.1-mini
```

Outputs: `data/results/week_XX/<model>/{neutral,stylized,decoupled}.json`. Each file holds the seven daily intermediates plus the Day-7 weekly magazine.

> Note: the script's argparse default model is `groq-llama-70b` (a legacy from the original protocol). Pass `--model openai-4o-mini` or `--model openai-4.1-mini` explicitly. Groq is not used in the published results.

### Step 3 — Run the two-judge LLM evaluator

```bash
python judge.py --artifact weekly_magazine \
                --judge_model openai-4o-mini \
                --gen_model openai-4o-mini

python judge.py --artifact weekly_magazine \
                --judge_model openai-4o-mini \
                --gen_model openai-4.1-mini \
                --out data/judgments/gpt41mini
```

Outputs: `data/judgments/judgments_weekly_magazine_openai-4o-mini.csv` (and the `gpt41mini/` mirror). One row per (week, pipeline, fact) with `verdict_strict`, `verdict_lenient`, and supporting evidence snippets. Both judges run with `temperature=0.0`.

### Step 4 — Statistical analysis

```bash
python stats_analysis.py \
  --judgments data/judgments/judgments_weekly_magazine_openai-4o-mini.csv \
  --out figures
```

Outputs in `figures/`:
- `stats_overall.csv` — per-pipeline mean preservation + 95% bootstrap CIs (10,000 resamples, week-level).
- `stats_decay_by_day.csv` — preservation rate by day-of-origin (the central diagnostic).
- `stats_paired_tests.csv` — paired Wilcoxon signed-rank tests on per-week rates.

### Step 5 — Figures

```bash
python analyze.py --judgments data/judgments/judgments_weekly_magazine_openai-4o-mini.csv
python polish_figures.py
python build_combined_figure.py   # side-by-side primary + cross-model
```

Outputs in `figures/`: `fig1_decay_strict.png` (Figure 2 in the paper), `fig1_decay_lenient.png` (Figure 4), `fig2_decay_by_type_strict.png` (Figure 3), and the polished variants. CI-banded versions are produced by `analyze.py` directly.

### Step 6 — Aggregate metrics (RQ3)

```bash
python metrics_auto.py --geval
```

Output: `data/judgments/automatic_metrics.csv`, one row per (week, pipeline, gen_model) with `rouge1_f`, `rouge2_f`, `rougeL_f`, `bertscore_p/r/f`, and four G-Eval scores (`faithfulness`, `fluency`, `style_adherence`, `overall_quality`). Run on the primary model only; not regenerated for the cross-model run.

### Step 7 — Token-budget ablation (Section 4.5)

```bash
python ablation_budget.py
python judge.py --artifact weekly_magazine \
                --pipelines stylized_1000tok \
                --out data/judgments/ablation
```

Re-runs stylized at `max_tokens=1000` on weeks 1, 4, 8, 11, 15 to verify that decoupled's advantage is architectural and not due to its larger render budget. At 1000 tokens, stylized preserves 24.5% (vs 28.2% at 600); the larger budget does not rescue the pipeline.

### Step 8 — Human validation

```bash
streamlit run spot_check.py            # each reviewer rates 17 items
python analyze_spotcheck.py            # writes figures/human_validation.txt
```

Three reviewers (the authors) independently rate the same 17 stratified-random (fact, magazine) pairs (seed = 42). Output: `data/judgments/human_spotcheck.csv` and `figures/human_validation.txt` with human–LLM agreement, pairwise inter-rater κ, and lists of items where humans and the LLM disagree.

---

## Data schemas

### Week (`data/weeks/week_XX.json`)

```json
{
  "week_id": 1,
  "persona": "A 35-year-old physiotherapist in Oslo who also competes in amateur long-distance ...",
  "facts": [
    {"id": "f01", "day": 1, "type": "quantitative", "text": "ran 10 kilometers on Monday"}
  ],
  "facts_by_day": {"1": [...], "2": [...], "...": "...", "7": [...]},
  "transcripts": {"1": "Snap: ...\nStar: ...", "...": "...", "7": "..."}
}
```

Fact types: `named_entity`, `quantitative`, `relational`, `emotional`. Each type is required to appear at least three times per week. Across 15 weeks the corpus contains **327 facts**.

### Pipeline output (`data/results/week_XX/<model>/<pipeline>.json`)

```json
{
  "pipeline": "neutral",
  "model": "openai-4o-mini",
  "daily_summaries": {"1": "...", "2": "...", "...": "...", "7": "..."},
  "weekly_magazine": "..."
}
```

### Judgment CSV (`data/judgments/judgments_weekly_magazine_openai-4o-mini.csv`)

One row per `(week_id, pipeline, gen_model, fact_id)`. Key columns: `fact_day`, `fact_type`, `verdict_strict`, `verdict_lenient`, `evidence_strict`, `evidence_lenient`. Both verdicts ∈ {`YES`, `NO`, `UNCLEAR`}; for analysis, `UNCLEAR` collapses to `NO`.

---

## Models and parameters (frozen)

| Component                      | Model            | Temperature | Max tokens |
| ------------------------------ | ---------------- | :---------: | :--------: |
| Week planner (synthetic_weeks) | `openai-4o-mini` | 0.7         | 1500       |
| Daily interview generator      | `openai-4o-mini` | 0.7         | 1500       |
| Neutral / stylized summarizer  | (per `--model`)  | 0.7         | 600        |
| Decoupled state updater        | (per `--model`)  | 0.7         | 900        |
| Decoupled magazine renderer    | (per `--model`)  | 0.7         | 1000       |
| LLM judge (both prompts)       | `openai-4o-mini` | 0.0         | —          |

Pipeline generation models: **primary** = `openai-4o-mini`, **cross-model** = `openai-4.1-mini`. The judge is the same for both runs, so any change in measured preservation rates is attributable to the change in generation model.

Total API spend across all generation, judging, and evaluation runs: under \$10.

---

## Known limitations

- Findings are established on two models from the same vendor family (`gpt-4o-mini`, `gpt-4.1-mini`). The original protocol planned a cross-vendor run; upstream access constraints made it infeasible within the project window. The per-step-paraphrase mechanism in §5 of the paper is model-agnostic and we expect the pattern to generalize, but this is not directly tested.
- One persona type (Vogue-meets-tabloid Paparazzo) was tested. Other strong-voice personas are predicted to produce similar compounding decay; not verified.
- 15 synthetic personas, not real users. The synthetic protocol is what makes the pre-registered day-of-origin probe possible.
- Seven-day horizon. Longer horizons may force a periodic state-consolidation step that could reintroduce compression.
- The strict LLM judge has only moderate human agreement (κ = 0.549) because its verbatim-paraphrase requirement is stricter than what humans naturally apply. The lenient judge (κ = 0.850) is the validated primary measurement; strict values are reported alongside as a robustness check.

---

## Citation

If you use this code, the corpus, or the day-of-origin diagnostic, please cite:

> Daruka, A., Oak, M., & Sen, R. (2026). When the Voice Erases the Memory: Compounding Fact Decay in Recursive Stylized Diary Summarization. Otto von Guericke University Magdeburg.

Repository: <https://github.com/medhinioakovgu/star-diary>
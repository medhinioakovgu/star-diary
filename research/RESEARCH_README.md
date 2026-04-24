# Star-Diary Research Pipeline — Quick Reference

This directory contains the research code for measuring fact-decay in recursive stylized summarization. Run the scripts in the order shown below.

## One-time setup (do this once)

From the `star-diary` repo root:

```bash
# 1. Activate your virtual environment (if you already have one)
source .venv/bin/activate       # macOS/Linux
# OR
.venv\Scripts\activate          # Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create/edit .env file in the repo root with these two lines:
#      GROQ_API_KEY=gsk_xxxxxxxxxxxxx
#      OPENAI_API_KEY=sk-xxxxxxxxxxxxx   (optional for now)
```

## The full research run

All commands are run from inside `research/`:

```bash
cd research
```

### Step 1: Smoke test your API key

```bash
python llm_client.py
```
Expected output: something like `Reply: hello research team`. If you get an error about `GROQ_API_KEY not set`, fix `.env` and try again.

### Step 2: Generate synthetic weeks

```bash
# Test with 2 weeks first
python synthetic_weeks.py --count 2

# If those look good, generate the full set
python synthetic_weeks.py --count 15
```
Outputs: `data/weeks/week_01.json` through `week_15.json`. Each file contains persona, fact list, and 7 daily interview transcripts. Open one and read it to make sure the interviews look realistic.

### Step 3: Run the three pipelines on the weeks

```bash
# Test with one week first
python pipelines.py --week 1

# If outputs look good, run everything
python pipelines.py
```
Outputs: `data/results/week_XX/<model>/<pipeline>.json`. Each file has 7 daily summaries and a weekly magazine.

### Step 4: Judge the weekly magazines

```bash
python judge.py --artifact weekly_magazine
```
Output: `data/judgments/judgments_weekly_magazine_groq-llama-70b.csv`. One row per (week, pipeline, fact) with two verdicts (strict/lenient).

### Step 5: Analyze and plot

```bash
python analyze.py --judgments data/judgments/judgments_weekly_magazine_groq-llama-70b.csv
```
Outputs in `figures/`:
- `fig1_decay_strict.png` — the headline figure (decay curves, strict judge)
- `fig1_decay_lenient.png` — same, lenient judge
- `fig2_decay_by_type_strict.png` — decay curves broken down by fact type
- `summary_table.csv` — overall preservation rate per pipeline
- `interjudge_agreement.txt` — Cohen's kappa between judges

## What to do after Day 5

- **Cross-model robustness:** run pipelines with OpenAI: `python pipelines.py --model openai-4o-mini --week 1 --week 2 ... --week 5`. Then judge and analyze separately.
- **Daily evaluation (if there's time):** run `python judge.py --artifact all_daily` to get per-day decay curves, not just the Day-7 endpoint.
- **Smaller-model check:** if results are flat, run with `--model groq-llama-8b`.

## Troubleshooting

**"API error: rate limit"** — Groq has free-tier rate limits. Add `time.sleep(1)` between calls in `pipelines.py` if you hit it, or wait a minute and rerun.

**Judge returns empty JSON** — Rare; the code handles it by marking facts as UNCLEAR. If it happens often, inspect `logs/llm_calls.jsonl` for the raw output and tune `_parse_judge_output` in `judge.py`.

**Week generation crashes mid-way** — Scripts skip existing files, so just re-run.

**Need to redo a single week** — Delete the relevant files under `data/results/week_XX/` and re-run `pipelines.py`.

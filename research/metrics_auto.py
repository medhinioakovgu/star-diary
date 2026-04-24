"""
metrics_auto.py -- Automatic metrics for the Star-Diary research pipeline.

Computes ROUGE and BERTScore between each pipeline's weekly_magazine and the
raw interview transcripts for that week (RQ3 secondary analysis).

G-Eval scoring (Day 4) is activated with --geval. It calls the LLM to score
each magazine on faithfulness, fluency, style adherence, and overall quality.

The hypothesis behind RQ3: automatic metrics will NOT distinguish between
pipelines the way the fact-decay curve does. A flat ROUGE/BERTScore table
across neutral/stylized/decoupled is actually the EXPECTED result — it
demonstrates that these metrics are blind to fact-level decay.

Output:
    data/judgments/automatic_metrics.csv
    One row per (week_id, pipeline, gen_model) with all metric columns.

Usage:
    cd research/

    # Day 3 — ROUGE + BERTScore only (fast)
    python metrics_auto.py

    # Day 4 — add G-Eval scoring (~300 extra API calls, ~10 min)
    python metrics_auto.py --geval

    # Skip BERTScore if too slow on your machine
    python metrics_auto.py --no-bertscore
"""

from __future__ import annotations

import argparse
import csv
import json
import pathlib
import sys
import time
from typing import Optional

# ── PATHS ─────────────────────────────────────────────────────────────────────
BASE          = pathlib.Path(__file__).parent
WEEKS_DIR     = BASE / "data" / "weeks"
RESULTS_DIR   = BASE / "data" / "results"
JUDGMENTS_DIR = BASE / "data" / "judgments"
OUTPUT_CSV    = JUDGMENTS_DIR / "automatic_metrics.csv"

PIPELINES  = ["neutral", "stylized", "decoupled"]
GEVAL_DIMS = ["faithfulness", "fluency", "style_adherence", "overall_quality"]

CSV_FIELDS = [
    "week_id", "pipeline", "gen_model",
    "rouge1_f", "rouge2_f", "rougeL_f",
    "bertscore_p", "bertscore_r", "bertscore_f",
] + [f"geval_{dim}" for dim in GEVAL_DIMS]


# ── DATA LOADING ──────────────────────────────────────────────────────────────
def load_week(week_id: int) -> dict:
    path = WEEKS_DIR / f"week_{week_id:02d}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def load_result(week_id: int, pipeline: str, gen_model: str) -> Optional[dict]:
    path = RESULTS_DIR / f"week_{week_id:02d}" / gen_model / f"{pipeline}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def get_reference_text(week: dict) -> str:
    """Concatenate all 7 daily transcripts as the reference for ROUGE/BERTScore."""
    transcripts = week.get("transcripts", {})
    return "\n\n".join(transcripts[str(d)] for d in range(1, 8) if str(d) in transcripts)


def discover_model_dirs(week_id: int) -> list[str]:
    """Return list of generation-model directory names for a given week."""
    week_dir = RESULTS_DIR / f"week_{week_id:02d}"
    if not week_dir.exists():
        return []
    return [d.name for d in week_dir.iterdir() if d.is_dir()]


# ── ROUGE ─────────────────────────────────────────────────────────────────────
def compute_rouge(hypothesis: str, reference: str) -> dict[str, float]:
    """
    Returns ROUGE-1, ROUGE-2, ROUGE-L F1 scores.
    Requires: pip install rouge-score
    """
    try:
        from rouge_score import rouge_scorer
    except ImportError:
        print("rouge-score not installed. Run: pip install rouge-score")
        sys.exit(1)

    scorer = rouge_scorer.RougeScorer(["rouge1", "rouge2", "rougeL"], use_stemmer=True)
    scores = scorer.score(reference, hypothesis)
    return {
        "rouge1_f": round(scores["rouge1"].fmeasure, 4),
        "rouge2_f": round(scores["rouge2"].fmeasure, 4),
        "rougeL_f": round(scores["rougeL"].fmeasure, 4),
    }


# ── BERTSCORE ────────────────────────────────────────────────────────────────
def compute_bertscore(hypotheses: list[str], references: list[str]) -> list[dict[str, float]]:
    """
    Computes BERTScore P/R/F for a batch of (hypothesis, reference) pairs.
    Batched to save time on model loading.
    Requires: pip install bert-score
    """
    try:
        from bert_score import score as bert_score_fn
    except ImportError:
        print("bert-score not installed. Run: pip install bert-score")
        sys.exit(1)

    print("  Computing BERTScore (this downloads a model on first run)...")
    P, R, F = bert_score_fn(
        hypotheses, references,
        lang="en",
        model_type="distilbert-base-uncased",   # fast; swap to roberta-large for final paper
        verbose=False,
    )
    results = []
    for p, r, f in zip(P.tolist(), R.tolist(), F.tolist()):
        results.append({
            "bertscore_p": round(p, 4),
            "bertscore_r": round(r, 4),
            "bertscore_f": round(f, 4),
        })
    return results


# ── G-EVAL ────────────────────────────────────────────────────────────────────
GEVAL_SYSTEM = """\
You are an expert evaluator of text summaries. You will be given a weekly magazine article
and the raw interview transcripts it was based on. Score the article on each of the four
dimensions below. Return ONLY a JSON object with integer scores 1-5 for each dimension.

Scoring dimensions:
  faithfulness      -- How faithfully does the article reflect the facts from the raw transcripts?
                       1 = major fabrications or omissions, 5 = all key facts accurately represented.
  fluency           -- Is the article well-written, grammatical, and easy to read?
                       1 = hard to read, 5 = polished and fluent.
  style_adherence   -- How well does the article match its intended style?
                       For a neutral article: 1 = very dramatic/biased, 5 = perfectly neutral/factual.
                       For a stylized/dramatic article: 1 = bland/neutral, 5 = vivid tabloid voice.
  overall_quality   -- Overall, how good is this summary as a weekly review of someone's life?
                       1 = poor, 5 = excellent.

Return ONLY a JSON object like:
{"faithfulness": 4, "fluency": 5, "style_adherence": 3, "overall_quality": 4}
No preamble, no explanation, no code fences.
"""


def compute_geval(
    magazine: str,
    reference: str,
    pipeline: str,
    week_id: int,
    gen_model: str,
) -> dict[str, float]:
    """
    G-Eval: LLM-as-judge for holistic quality dimensions.
    Returns dict of dimension -> score (1-5), or NaN on failure.
    """
    try:
        from llm_client import chat
    except ImportError:
        print("llm_client not found. Run from inside research/ directory.")
        sys.exit(1)

    style_note = (
        "Note: this is a NEUTRAL pipeline — score style_adherence=5 if the article is factual "
        "and neutral, score lower if it is dramatic or editorialised."
        if pipeline == "neutral" else
        "Note: this is a STYLIZED/DRAMATIC pipeline — score style_adherence=5 if the article "
        "has a vivid tabloid voice, score lower if it reads as bland or purely factual."
    )

    user_msg = (
        f"PIPELINE: {pipeline}\n{style_note}\n\n"
        f"RAW INTERVIEW TRANSCRIPTS (reference):\n{reference[:3000]}\n\n"
        f"WEEKLY MAGAZINE ARTICLE (to evaluate):\n{magazine[:2000]}"
    )

    try:
        reply = chat(
            system=GEVAL_SYSTEM,
            messages=[{"role": "user", "content": user_msg}],
            model="openai-4o-mini",
            temperature=0.0,
            max_tokens=100,
            tag=f"geval_w{week_id:02d}_{pipeline}_{gen_model}",
        )
        # Parse JSON from response
        text = reply.strip()
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        scores = json.loads(text.strip())
        return {f"geval_{k}": float(scores.get(k, float("nan"))) for k in GEVAL_DIMS}
    except Exception as e:
        print(f"    [G-Eval] Error for w{week_id:02d}/{pipeline}/{gen_model}: {e}")
        return {f"geval_{k}": float("nan") for k in GEVAL_DIMS}


# ── LOAD EXISTING RESULTS ─────────────────────────────────────────────────────
def load_existing(csv_path: pathlib.Path) -> set[tuple]:
    """Return set of (week_id, pipeline, gen_model) already processed."""
    if not csv_path.exists():
        return set()
    with open(csv_path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return {(int(r["week_id"]), r["pipeline"], r["gen_model"]) for r in rows}


# ── MAIN ─────────────────────────────────────────────────────────────────────
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compute ROUGE, BERTScore, and optional G-Eval for all pipeline outputs."
    )
    parser.add_argument(
        "--geval", action="store_true",
        help="Add G-Eval scoring via LLM (adds ~300 API calls). Day 4 task.",
    )
    parser.add_argument(
        "--no-bertscore", action="store_true",
        help="Skip BERTScore (saves time; add back before final submission).",
    )
    parser.add_argument(
        "--weeks", nargs="+", type=int, default=None,
        help="Run only specific week IDs, e.g. --weeks 1 2 3. Default: all.",
    )
    args = parser.parse_args()

    JUDGMENTS_DIR.mkdir(parents=True, exist_ok=True)
    already_done = load_existing(OUTPUT_CSV)

    # Collect all (week_id, gen_model) pairs from results directory
    all_week_dirs = sorted(RESULTS_DIR.glob("week_*"))
    targets: list[tuple[int, str]] = []
    for wd in all_week_dirs:
        wid = int(wd.name.replace("week_", ""))
        if args.weeks and wid not in args.weeks:
            continue
        for model_dir in sorted(wd.iterdir()):
            if model_dir.is_dir():
                targets.append((wid, model_dir.name))

    if not targets:
        print("No result files found. Check data/results/ directory.")
        sys.exit(1)

    # ── Batch BERTScore setup ─────────────────────────────────────────────────
    # Collect all (hypothesis, reference) pairs first, then call BERTScore once.
    batch_hyps:  list[str]   = []
    batch_refs:  list[str]   = []
    batch_keys:  list[tuple] = []   # (week_id, pipeline, gen_model)

    rows_to_write: list[dict] = []

    print(f"Processing {len(targets)} (week, model) combinations × {len(PIPELINES)} pipelines...\n")

    for week_id, gen_model in targets:
        try:
            week = load_week(week_id)
        except FileNotFoundError:
            print(f"  Week file not found for week {week_id:02d}, skipping.")
            continue
        reference = get_reference_text(week)

        for pipeline in PIPELINES:
            key = (week_id, pipeline, gen_model)
            if key in already_done:
                print(f"  week {week_id:02d} / {pipeline} / {gen_model} — already done, skipping.")
                continue

            result = load_result(week_id, pipeline, gen_model)
            if result is None:
                print(f"  week {week_id:02d} / {pipeline} / {gen_model} — result file missing.")
                continue

            magazine = result.get("weekly_magazine", "")
            if not magazine.strip():
                print(f"  week {week_id:02d} / {pipeline} / {gen_model} — empty magazine, skipping.")
                continue

            print(f"  week {week_id:02d} / {pipeline} / {gen_model}...", end=" ")

            # ROUGE (fast, compute inline)
            rouge_scores = compute_rouge(magazine, reference)
            print(f"ROUGE-1={rouge_scores['rouge1_f']:.3f}", end=" ")

            row: dict = {
                "week_id":   week_id,
                "pipeline":  pipeline,
                "gen_model": gen_model,
                **rouge_scores,
                # BERTScore filled in after batch call
                "bertscore_p": None,
                "bertscore_r": None,
                "bertscore_f": None,
                # G-Eval filled in if --geval
                **{f"geval_{d}": None for d in GEVAL_DIMS},
            }

            if not args.no_bertscore:
                batch_hyps.append(magazine)
                batch_refs.append(reference)
                batch_keys.append(key)

            if args.geval:
                geval_scores = compute_geval(magazine, reference, pipeline, week_id, gen_model)
                row.update(geval_scores)
                print(f"G-Eval faithfulness={geval_scores.get('geval_faithfulness', '?')}", end=" ")
                time.sleep(0.5)   # rate-limit politeness

            print("✓")
            rows_to_write.append(row)

    # ── Batch BERTScore ───────────────────────────────────────────────────────
    if not args.no_bertscore and batch_hyps:
        print(f"\nRunning BERTScore on {len(batch_hyps)} items (batch)...")
        bs_results = compute_bertscore(batch_hyps, batch_refs)
        key_to_bs  = dict(zip(batch_keys, bs_results))
        for row in rows_to_write:
            key = (row["week_id"], row["pipeline"], row["gen_model"])
            if key in key_to_bs:
                row.update(key_to_bs[key])

    # ── Write CSV ─────────────────────────────────────────────────────────────
    if rows_to_write:
        write_header = not OUTPUT_CSV.exists()
        with open(OUTPUT_CSV, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDS, extrasaction="ignore")
            if write_header:
                writer.writeheader()
            writer.writerows(rows_to_write)
        print(f"\n💾 Appended {len(rows_to_write)} rows to {OUTPUT_CSV}")
    else:
        print("\nNo new rows to write (all already processed).")

    # ── Summary table ─────────────────────────────────────────────────────────
    print("\n── Summary by pipeline ──────────────────────────────────────────")
    _print_summary(OUTPUT_CSV)


def _print_summary(csv_path: pathlib.Path) -> None:
    """Print mean metrics per pipeline."""
    if not csv_path.exists():
        print("No output file found.")
        return

    with open(csv_path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    from collections import defaultdict
    by_pipeline: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_pipeline[r["pipeline"]].append(r)

    def safe_mean(vals):
        nums = [float(v) for v in vals if v not in (None, "", "None", "nan")]
        return sum(nums) / len(nums) if nums else float("nan")

    header = f"{'Pipeline':<12} {'ROUGE-1':>8} {'ROUGE-2':>8} {'ROUGE-L':>8} {'BS-F':>8} {'GEval-Faith':>12}"
    print(header)
    print("-" * len(header))
    for pipe in sorted(by_pipeline):
        rs = by_pipeline[pipe]
        r1  = safe_mean(r.get("rouge1_f")     for r in rs)
        r2  = safe_mean(r.get("rouge2_f")     for r in rs)
        rl  = safe_mean(r.get("rougeL_f")     for r in rs)
        bsf = safe_mean(r.get("bertscore_f")  for r in rs)
        gf  = safe_mean(r.get("geval_faithfulness") for r in rs)
        print(f"{pipe:<12} {r1:>8.3f} {r2:>8.3f} {rl:>8.3f} {bsf:>8.3f} {gf:>12.2f}")

    print(f"\nFull results: {csv_path}")
    print(
        "\nExpected finding for RQ3: ROUGE and BERTScore show similar scores across "
        "pipelines, while the fact-decay curve (judge.py output) reveals the gap. "
        "If that's what you see, the table is a positive result for the paper."
    )


if __name__ == "__main__":
    main()
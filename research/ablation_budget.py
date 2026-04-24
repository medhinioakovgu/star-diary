"""
ablation_budget.py -- Token-budget ablation for the stylized pipeline.

Runs the stylized recursive summarizer with max_tokens=1000 instead of 600,
on 5 specified weeks, to test whether catastrophic fact loss under stylization
is budget-driven or architecture-driven.

Outputs to research/data/results/week_XX/<model>/stylized_1000tok.json to
keep it visually distinct from the main stylized.json outputs.

Usage:
    cd research
    python ablation_budget.py --weeks 1 4 8 11 15 --model openai-4o-mini
"""

import argparse
import json
import pathlib
from llm_client import chat
from prompts import STYLIZED_SUMMARIZER_PROMPT
from pipelines import _build_update_message


def update_stylized_1000tok(prev_summary: str, today_transcript: str, day: int, model: str) -> str:
    """Same as pipelines.update_stylized but with max_tokens=1000 instead of 600."""
    user_msg = _build_update_message(prev_summary, today_transcript, day)
    return chat(
        system=STYLIZED_SUMMARIZER_PROMPT,
        messages=[{"role": "user", "content": user_msg}],
        model=model,
        temperature=0.7,
        max_tokens=1000,
        tag=f"stylized_1000tok_day{day}",
    )


def run_pipeline_stylized_1000tok(week: dict, model: str) -> dict:
    summaries = {}
    prev = ""
    for day in range(1, 8):
        transcript = week["transcripts"][str(day)]
        prev = update_stylized_1000tok(prev, transcript, day, model=model)
        summaries[str(day)] = prev
    return {
        "pipeline": "stylized_1000tok",
        "model": model,
        "daily_summaries": summaries,
        "weekly_magazine": summaries["7"],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--weeks", nargs="+", type=int, required=True,
                        help="Week IDs to run (e.g. --weeks 1 4 8 11 15)")
    parser.add_argument("--model", default="openai-4o-mini",
                        help="Model to use (default: openai-4o-mini, matching main results)")
    parser.add_argument("--weeks_dir", default="data/weeks")
    parser.add_argument("--out", default="data/results")
    args = parser.parse_args()

    weeks_dir = pathlib.Path(__file__).parent / args.weeks_dir
    out_root = pathlib.Path(__file__).parent / args.out

    for week_id in args.weeks:
        wf = weeks_dir / f"week_{week_id:02d}.json"
        if not wf.exists():
            print(f"[week {week_id:02d}] week file not found, skipping.")
            continue
        week = json.loads(wf.read_text(encoding="utf-8"))
        out_dir = out_root / f"week_{week_id:02d}" / args.model
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "stylized_1000tok.json"
        if out_path.exists():
            print(f"[week {week_id:02d} / stylized_1000tok / {args.model}] already exists, skipping.")
            continue
        print(f"[week {week_id:02d} / stylized_1000tok / {args.model}] running...")
        result = run_pipeline_stylized_1000tok(week, model=args.model)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"  Saved to {out_path}")

    print("\nAblation run complete.")


if __name__ == "__main__":
    main()
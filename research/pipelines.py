"""
pipelines.py -- The three summarization pipelines that are the subject of RQ1, RQ2, RQ3.

Pipeline A (neutral):    neutral voice, free-prose recursive summary
Pipeline B (stylized):   Paparazzo voice, free-prose recursive summary
Pipeline C (decoupled):  neutral structured state (daily) + Paparazzo render (Day 7 only)

Each pipeline consumes one synthetic week (from synthetic_weeks.py) and produces
7 daily summaries plus (for pipeline C) a final weekly magazine.

For pipelines A and B, the "weekly magazine" is simply the Day-7 summary,
which is the recursive output at the end of the week. Pipeline C produces a
separate magazine by rendering the final state with the Paparazzo voice.

Usage:
    python pipelines.py --weeks_dir data/weeks --out results
"""

import argparse
import json
import pathlib
from llm_client import chat
from prompts import (
    NEUTRAL_SUMMARIZER_PROMPT,
    STYLIZED_SUMMARIZER_PROMPT,
    DECOUPLED_STATE_UPDATE_PROMPT,
    DECOUPLED_MAGAZINE_RENDER_PROMPT,
)


# ---------------------------------------------------------------------------
# The three recursive update functions. Each takes (prev, today_transcript)
# and returns the new summary/state.
# ---------------------------------------------------------------------------
def update_neutral(prev_summary: str, today_transcript: str, day: int, model: str) -> str:
    user_msg = _build_update_message(prev_summary, today_transcript, day)
    return chat(
        system=NEUTRAL_SUMMARIZER_PROMPT,
        messages=[{"role": "user", "content": user_msg}],
        model=model,
        temperature=0.7,
        max_tokens=600,
        tag=f"neutral_day{day}",
    )


def update_stylized(prev_summary: str, today_transcript: str, day: int, model: str) -> str:
    user_msg = _build_update_message(prev_summary, today_transcript, day)
    return chat(
        system=STYLIZED_SUMMARIZER_PROMPT,
        messages=[{"role": "user", "content": user_msg}],
        model=model,
        temperature=0.7,
        max_tokens=600,
        tag=f"stylized_day{day}",
    )


def update_decoupled_state(prev_state: str, today_transcript: str, day: int, model: str) -> str:
    user_msg = _build_update_message(prev_state, today_transcript, day)
    return chat(
        system=DECOUPLED_STATE_UPDATE_PROMPT,
        messages=[{"role": "user", "content": user_msg}],
        model=model,
        temperature=0.7,
        max_tokens=900,
        tag=f"decoupled_state_day{day}",
    )


def render_decoupled_magazine(final_state: str, model: str) -> str:
    user_msg = f"Here is the dossier:\n\n{final_state}"
    return chat(
        system=DECOUPLED_MAGAZINE_RENDER_PROMPT,
        messages=[{"role": "user", "content": user_msg}],
        model=model,
        temperature=0.7,
        max_tokens=1000,
        tag="decoupled_magazine_render",
    )


def _build_update_message(prev: str, transcript: str, day: int) -> str:
    if day == 1:
        return (
            f"This is Day 1 of the week, so there is no previous summary.\n\n"
            f"Today's interview transcript:\n{transcript}"
        )
    return (
        f"Previous summary (from Day {day - 1}):\n{prev}\n\n"
        f"Today's interview transcript (Day {day}):\n{transcript}"
    )


# ---------------------------------------------------------------------------
# Full-week runners -- one per pipeline. Each returns a dict of daily outputs.
# ---------------------------------------------------------------------------
def run_pipeline_neutral(week: dict, model: str) -> dict:
    summaries = {}
    prev = ""
    for day in range(1, 8):
        transcript = week["transcripts"][str(day)]
        prev = update_neutral(prev, transcript, day, model=model)
        summaries[str(day)] = prev
    return {
        "pipeline": "neutral",
        "model": model,
        "daily_summaries": summaries,
        "weekly_magazine": summaries["7"],  # Day 7 output IS the magazine for this pipeline
    }


def run_pipeline_stylized(week: dict, model: str) -> dict:
    summaries = {}
    prev = ""
    for day in range(1, 8):
        transcript = week["transcripts"][str(day)]
        prev = update_stylized(prev, transcript, day, model=model)
        summaries[str(day)] = prev
    return {
        "pipeline": "stylized",
        "model": model,
        "daily_summaries": summaries,
        "weekly_magazine": summaries["7"],
    }


def run_pipeline_decoupled(week: dict, model: str) -> dict:
    states = {}
    prev = ""
    for day in range(1, 8):
        transcript = week["transcripts"][str(day)]
        prev = update_decoupled_state(prev, transcript, day, model=model)
        states[str(day)] = prev
    magazine = render_decoupled_magazine(states["7"], model=model)
    return {
        "pipeline": "decoupled",
        "model": model,
        "daily_summaries": states,  # note: these are structured states, not free prose
        "weekly_magazine": magazine,
    }


PIPELINE_RUNNERS = {
    "neutral": run_pipeline_neutral,
    "stylized": run_pipeline_stylized,
    "decoupled": run_pipeline_decoupled,
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--weeks_dir", default="data/weeks",
                        help="Directory with week_XX.json files.")
    parser.add_argument("--out", default="data/results",
                        help="Output directory for pipeline results.")
    parser.add_argument("--model", default="groq-llama-70b",
                        help="Model to use for all pipelines.")
    parser.add_argument("--pipelines", nargs="+",
                        default=["neutral", "stylized", "decoupled"],
                        help="Which pipelines to run.")
    parser.add_argument("--week", type=int, default=None,
                        help="Run only this week id (1-indexed). Default: all weeks found.")
    args = parser.parse_args()

    weeks_dir = pathlib.Path(__file__).parent / args.weeks_dir
    out_root = pathlib.Path(__file__).parent / args.out
    out_root.mkdir(parents=True, exist_ok=True)

    week_files = sorted(weeks_dir.glob("week_*.json"))
    if args.week is not None:
        week_files = [f for f in week_files if f.stem == f"week_{args.week:02d}"]
        if not week_files:
            print(f"No week file matching --week {args.week}")
            return

    for wf in week_files:
        week = json.loads(wf.read_text(encoding="utf-8"))
        week_id = week["week_id"]
        for pipeline_name in args.pipelines:
            out_dir = out_root / f"week_{week_id:02d}" / args.model
            out_dir.mkdir(parents=True, exist_ok=True)
            out_path = out_dir / f"{pipeline_name}.json"
            if out_path.exists():
                print(f"[week {week_id:02d} / {pipeline_name} / {args.model}] already exists, skipping.")
                continue
            print(f"[week {week_id:02d} / {pipeline_name} / {args.model}] running...")
            runner = PIPELINE_RUNNERS[pipeline_name]
            result = runner(week, model=args.model)
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"    Saved to {out_path}")

    print("\nAll pipeline runs complete.")


if __name__ == "__main__":
    main()

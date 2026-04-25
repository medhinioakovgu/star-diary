"""
fix_neutral_truncation_4_1mini.py
==================================
Companion to fix_neutral_truncation.py (Medhini's, scoped to openai-4o-mini).

Same bug, different model: pipelines.update_neutral() runs at max_tokens=600,
which can truncate the Day-7 neutral magazine on weeks where the accumulated
summary exceeds the cap. For the openai-4.1-mini cross-model robustness run
(Upgrade A), only week 15 was affected — but this script accepts --model and
auto-detects truncated weeks so it generalizes if other weeks are affected
on a future run.

Why a separate script: pipelines.py is FROZEN, fix_neutral_truncation.py is
Medhini's territory and hardcodes openai-4o-mini at module level. The
pipeline-owner-territory equivalent for other models lives here.

Behavior matches Medhini's script:
  - Imports the frozen NEUTRAL_SUMMARIZER_PROMPT and llm_client.chat
  - Re-runs the neutral pipeline at max_tokens=2000
  - Backs up the original truncated file as neutral.truncated_backup.json
  - Verifies the new output ends on a complete sentence before overwriting

Usage:
    cd research/
    python fix_neutral_truncation_4_1mini.py --check-only --model openai-4.1-mini
    python fix_neutral_truncation_4_1mini.py --model openai-4.1-mini
    python fix_neutral_truncation_4_1mini.py --model openai-4.1-mini --weeks 15
"""

from __future__ import annotations

import argparse
import json
import pathlib
import time

from llm_client import chat
from prompts import NEUTRAL_SUMMARIZER_PROMPT
from pipelines import _build_update_message  # frozen helper, imported not duplicated

BASE        = pathlib.Path(__file__).parent
WEEKS_DIR   = BASE / "data" / "weeks"
RESULTS_DIR = BASE / "data" / "results"
MAX_TOKENS_FIX = 2000


def is_truncated(text: str) -> bool:
    t = text.strip()
    return bool(t) and t[-1] not in ".!?\""


def scan_truncated(model: str) -> list[int]:
    """Return week IDs whose neutral magazine appears truncated, for the given model."""
    truncated: list[int] = []
    for wk_dir in sorted(RESULTS_DIR.glob("week_*")):
        neutral_path = wk_dir / model / "neutral.json"
        if not neutral_path.exists():
            continue
        data = json.loads(neutral_path.read_text())
        magazine = data.get("weekly_magazine", "")
        week_id = int(wk_dir.name.replace("week_", ""))
        if is_truncated(magazine):
            print(f"  Week {week_id:02d} TRUNCATED — ends: ...{magazine[-60:]!r}")
            truncated.append(week_id)
        else:
            print(f"  Week {week_id:02d} ok")
    return truncated


def run_neutral_fixed(week: dict, model: str) -> dict:
    """Mirror of pipelines.run_pipeline_neutral but at MAX_TOKENS_FIX."""
    week_id = week["week_id"]
    summaries: dict[str, str] = {}
    prev = ""
    for day in range(1, 8):
        transcript = week["transcripts"][str(day)]
        user_msg = _build_update_message(prev, transcript, day)
        prev = chat(
            system=NEUTRAL_SUMMARIZER_PROMPT,
            messages=[{"role": "user", "content": user_msg}],
            model=model,
            temperature=0.7,
            max_tokens=MAX_TOKENS_FIX,
            tag=f"fix_neutral_w{week_id:02d}_day{day}_{model}",
        )
        summaries[str(day)] = prev
        print(f"    Day {day} ✓  ({len(prev.split())} words)", end="\r")
        time.sleep(0.5)
    print()
    return {
        "pipeline": "neutral",
        "model": model,
        "daily_summaries": summaries,
        "weekly_magazine": summaries["7"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fix neutral pipeline truncation for non-default models (e.g. openai-4.1-mini)."
    )
    parser.add_argument("--model", required=True,
                        help="Model whose neutral outputs to scan/fix (e.g. openai-4.1-mini).")
    parser.add_argument("--check-only", action="store_true",
                        help="Scan and report truncated weeks without re-running.")
    parser.add_argument("--weeks", nargs="+", type=int, default=None,
                        help="Override which weeks to fix (default: auto-detected).")
    args = parser.parse_args()

    print(f"Scanning for truncated neutral magazines under model={args.model!r}...\n")
    detected = scan_truncated(args.model)
    print(f"\nDetected {len(detected)} truncated week(s): {detected}")

    if args.check_only:
        return

    weeks_to_fix = args.weeks if args.weeks is not None else detected
    if not weeks_to_fix:
        print("\nNo truncated weeks found — nothing to do.")
        return

    print(f"\nWill re-run neutral pipeline for weeks: {weeks_to_fix}")
    print(f"Model: {args.model}  |  max_tokens: {MAX_TOKENS_FIX}\n")
    confirm = input("Proceed? This will make API calls and overwrite result files. [y/N] ")
    if confirm.strip().lower() != "y":
        print("Aborted.")
        return

    for week_id in weeks_to_fix:
        week_path = WEEKS_DIR / f"week_{week_id:02d}.json"
        if not week_path.exists():
            print(f"  Week {week_id:02d}: week file not found, skipping.")
            continue

        out_path = RESULTS_DIR / f"week_{week_id:02d}" / args.model / "neutral.json"
        out_path.parent.mkdir(parents=True, exist_ok=True)

        week = json.loads(week_path.read_text())
        print(f"Re-running Week {week_id:02d} ({week.get('persona', '?')[:60]}...)")

        result = run_neutral_fixed(week, model=args.model)

        magazine = result["weekly_magazine"]
        if is_truncated(magazine):
            print(f"  ⚠ Week {week_id:02d} still appears truncated after fix!")
            print(f"    Ends: ...{magazine[-80:]!r}")
            print(f"    NOT overwriting. Investigate manually.")
            continue

        backup_path = out_path.with_suffix(".truncated_backup.json")
        if out_path.exists() and not backup_path.exists():
            backup_path.write_bytes(out_path.read_bytes())
            print(f"  Backup saved → {backup_path.name}")

        out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False))
        print(f"  ✓ Week {week_id:02d} fixed — magazine ends: ...{magazine[-60:]!r}")
        print()

    print(f"\nDone. Run with --check-only --model {args.model} to confirm all weeks are clean.")


if __name__ == "__main__":
    main()
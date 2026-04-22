"""
fix_neutral_truncation.py
==========================
One-shot fix for the neutral pipeline truncation bug.

Problem:  pipelines.py calls update_neutral() with max_tokens=600.
          By Day 7 the accumulated neutral summary can be 700+ tokens,
          so openai-4o-mini stops mid-sentence.

Fix:      Re-run the neutral pipeline for the 6 affected weeks using
          max_tokens=2000. Overwrite the truncated neutral.json files.
          Stylized and decoupled are NOT touched — they are fine.

Affected weeks: 1, 2, 3, 6, 8, 15  (detected by checking for sentences
                that do not end with . ! or ")

This script imports from llm_client and prompts (frozen files — not edited).
Run it from inside research/:

    cd research/
    python fix_neutral_truncation.py

After it finishes, check that no magazine ends mid-sentence:

    python fix_neutral_truncation.py --check-only
"""

from __future__ import annotations

import argparse
import json
import pathlib
import time

# Import from frozen team files (do not edit these)
from llm_client import chat
from prompts import NEUTRAL_SUMMARIZER_PROMPT

# ── CONFIG ────────────────────────────────────────────────────────────────────
BASE       = pathlib.Path(__file__).parent
WEEKS_DIR  = BASE / "data" / "weeks"
RESULTS_DIR= BASE / "data" / "results"

# The 6 weeks identified as truncated. Verify with --check-only first.
TRUNCATED_WEEKS = [1, 2, 3, 6, 8, 15]
GEN_MODEL       = "openai-4o-mini"   # must match the model that produced the results
MAX_TOKENS_FIX  = 2000               # was 600; neutral Day-7 summary needs room to breathe


# ── HELPERS ──────────────────────────────────────────────────────────────────
def is_truncated(text: str) -> bool:
    """Return True if the text appears to end mid-sentence."""
    t = text.strip()
    return bool(t) and t[-1] not in ".!?\""


def check_all_neutral_magazines() -> list[int]:
    """Scan all neutral weekly_magazine fields and return truncated week IDs."""
    truncated = []
    for wk_dir in sorted(RESULTS_DIR.glob("week_*")):
        neutral_path = wk_dir / GEN_MODEL / "neutral.json"
        if not neutral_path.exists():
            continue
        data = json.loads(neutral_path.read_text())
        magazine = data.get("weekly_magazine", "")
        if is_truncated(magazine):
            week_id = int(wk_dir.name.replace("week_", ""))
            print(f"  Week {week_id:02d} TRUNCATED — ends: ...{magazine[-60:]!r}")
            truncated.append(week_id)
        else:
            week_id = int(wk_dir.name.replace("week_", ""))
            print(f"  Week {week_id:02d} ok")
    return truncated


# ── NEUTRAL PIPELINE (with higher max_tokens) ─────────────────────────────────
def _build_message(prev: str, transcript: str, day: int) -> str:
    if day == 1:
        return (
            f"This is Day 1 of the week, so there is no previous summary.\n\n"
            f"Today's interview transcript:\n{transcript}"
        )
    return (
        f"Previous summary (from Day {day - 1}):\n{prev}\n\n"
        f"Today's interview transcript (Day {day}):\n{transcript}"
    )


def run_neutral_fixed(week: dict) -> dict:
    """
    Identical logic to pipelines.run_pipeline_neutral() but with
    max_tokens=MAX_TOKENS_FIX to prevent Day-7 truncation.
    Uses the same frozen NEUTRAL_SUMMARIZER_PROMPT.
    """
    week_id = week["week_id"]
    summaries: dict[str, str] = {}
    prev = ""

    for day in range(1, 8):
        transcript = week["transcripts"][str(day)]
        user_msg = _build_message(prev, transcript, day)

        prev = chat(
            system=NEUTRAL_SUMMARIZER_PROMPT,
            messages=[{"role": "user", "content": user_msg}],
            model=GEN_MODEL,
            temperature=0.7,
            max_tokens=MAX_TOKENS_FIX,
            tag=f"fix_neutral_w{week_id:02d}_day{day}",
        )
        summaries[str(day)] = prev
        print(f"    Day {day} ✓  ({len(prev.split())} words)", end="\r")
        time.sleep(0.5)   # rate-limit politeness

    print()  # newline after the \r progress
    return {
        "pipeline": "neutral",
        "model": GEN_MODEL,
        "daily_summaries": summaries,
        "weekly_magazine": summaries["7"],
    }


# ── MAIN ─────────────────────────────────────────────────────────────────────
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fix neutral pipeline truncation for affected weeks."
    )
    parser.add_argument(
        "--check-only", action="store_true",
        help="Scan and report truncated weeks without re-running anything.",
    )
    parser.add_argument(
        "--weeks", nargs="+", type=int, default=None,
        help="Override which weeks to fix (default: auto-detected truncated weeks).",
    )
    args = parser.parse_args()

    print("Scanning for truncated neutral magazines...\n")
    detected = check_all_neutral_magazines()
    print(f"\nDetected {len(detected)} truncated week(s): {detected}")

    if args.check_only:
        return

    weeks_to_fix = args.weeks if args.weeks is not None else detected
    if not weeks_to_fix:
        print("\nNo truncated weeks found — nothing to do.")
        return

    print(f"\nWill re-run neutral pipeline for weeks: {weeks_to_fix}")
    print(f"Model: {GEN_MODEL}  |  max_tokens: {MAX_TOKENS_FIX}\n")
    confirm = input("Proceed? This will make API calls and overwrite result files. [y/N] ")
    if confirm.strip().lower() != "y":
        print("Aborted.")
        return

    for week_id in weeks_to_fix:
        week_path = WEEKS_DIR / f"week_{week_id:02d}.json"
        if not week_path.exists():
            print(f"  Week {week_id:02d}: week file not found, skipping.")
            continue

        out_path = RESULTS_DIR / f"week_{week_id:02d}" / GEN_MODEL / "neutral.json"
        if not out_path.parent.exists():
            out_path.parent.mkdir(parents=True)

        week = json.loads(week_path.read_text())
        print(f"Re-running Week {week_id:02d} ({week['persona'][:60]}...)")

        result = run_neutral_fixed(week)

        # Verify the fix worked before overwriting
        magazine = result["weekly_magazine"]
        if is_truncated(magazine):
            print(f"  ⚠ Week {week_id:02d} still appears truncated after fix!")
            print(f"    Ends: ...{magazine[-80:]!r}")
            print(f"    NOT overwriting. Investigate manually.")
            continue

        # Backup original before overwriting
        backup_path = out_path.with_suffix(".truncated_backup.json")
        if out_path.exists() and not backup_path.exists():
            backup_path.write_bytes(out_path.read_bytes())
            print(f"  Backup saved → {backup_path.name}")

        out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False))
        print(f"  ✓ Week {week_id:02d} fixed — magazine ends: ...{magazine[-60:]!r}")
        print()

    print("\nDone. Run --check-only again to confirm all weeks are clean.")
    print("Then proceed with: python judge.py --artifact weekly_magazine")


if __name__ == "__main__":
    main()
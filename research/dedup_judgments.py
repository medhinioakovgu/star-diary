"""
dedup_judgments.py -- One-shot cleanup script to deduplicate the judgments CSV.

Problem: research/data/judgments/judgments_weekly_magazine_openai-4o-mini.csv was
produced by running judge.py twice (once on the initial corpus, once after the
neutral-truncation fix). judge.py opens the CSV in append mode, so the second run
wrote a second full set of rows instead of replacing the first. Result: most
(week, pipeline, fact) triples appear twice in the CSV, while the six neutral
weeks that were regenerated after the fix (1, 2, 3, 6, 8, 15) appear only once
because their first-run rows evaluated now-stale (truncated) summaries.

This script rewrites the CSV to keep exactly one row per (week, pipeline, fact),
preferring the LAST occurrence in the file (so that rows in the second run --
judged against the shipped, corrected outputs -- are preferred over any stale
first-run rows for other pipelines).

It also backs up the original CSV and writes a short audit log. Derived artifacts
(summary_table.csv, figures) must be regenerated separately by running
analyze.py and polish_figures.py after this script.

Running this script is IDEMPOTENT: running it twice on an already-cleaned CSV
produces the same output.

Usage:
    cd research
    python dedup_judgments.py
"""

import csv
import pathlib
import shutil
from datetime import datetime
from collections import defaultdict

HERE = pathlib.Path(__file__).parent
JUDGMENTS_CSV = HERE / "data" / "judgments" / "judgments_weekly_magazine_openai-4o-mini.csv"
BACKUP_DIR = HERE / "data" / "judgments" / "_backups"
AUDIT_LOG = HERE / "data" / "judgments" / "dedup_audit.log"


def backup_original():
    BACKUP_DIR.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"judgments_weekly_magazine_openai-4o-mini_predup_{ts}.csv"
    shutil.copy2(JUDGMENTS_CSV, backup_path)
    return backup_path


def load_rows(path):
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return reader.fieldnames, list(reader)


def dedup_last_wins(rows):
    """Keep only the last occurrence of each (week_id, pipeline, fact_id) triple."""
    keep = {}
    order = []  # preserve insertion order of first time we see each key
    for r in rows:
        key = (r["week_id"], r["pipeline"], r["fact_id"])
        if key not in keep:
            order.append(key)
        keep[key] = r
    return [keep[k] for k in order]


def write_rows(path, fieldnames, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def count_duplicates(rows):
    counts = defaultdict(int)
    for r in rows:
        counts[(r["week_id"], r["pipeline"], r["fact_id"])] += 1
    return {"total_rows": len(rows),
            "unique_triples": len(counts),
            "triples_with_2plus_rows": sum(1 for v in counts.values() if v >= 2),
            "triples_appearing_once": sum(1 for v in counts.values() if v == 1)}


def main():
    if not JUDGMENTS_CSV.exists():
        raise FileNotFoundError(f"Cannot find {JUDGMENTS_CSV}")

    print(f"Reading {JUDGMENTS_CSV}")
    fieldnames, rows_before = load_rows(JUDGMENTS_CSV)
    before_stats = count_duplicates(rows_before)
    print(f"  Before: {before_stats}")

    backup_path = backup_original()
    print(f"Backup written to: {backup_path}")

    rows_after = dedup_last_wins(rows_before)
    after_stats = count_duplicates(rows_after)
    print(f"  After:  {after_stats}")

    assert after_stats["total_rows"] == after_stats["unique_triples"], \
        "Dedup failed: some triples still duplicated after cleanup."
    assert after_stats["triples_with_2plus_rows"] == 0, \
        "Dedup failed: at least one triple still has 2+ rows."

    write_rows(JUDGMENTS_CSV, fieldnames, rows_after)
    print(f"Wrote {len(rows_after)} rows to {JUDGMENTS_CSV}")

    with open(AUDIT_LOG, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now().isoformat()}] dedup_judgments.py run\n")
        f.write(f"  backup: {backup_path.name}\n")
        f.write(f"  before: {before_stats}\n")
        f.write(f"  after:  {after_stats}\n\n")
    print(f"Audit log appended to: {AUDIT_LOG}")

    print("\nDedup complete. Next steps:")
    print("  1. Re-run analyze.py to regenerate figures and summary_table.csv")
    print("  2. Re-run polish_figures.py to regenerate publication-quality figures")
    print("  3. Verify the regenerated figures visually")
    print("  4. Commit changes")


if __name__ == "__main__":
    main()
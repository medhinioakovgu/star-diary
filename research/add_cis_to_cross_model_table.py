"""
add_cis_to_cross_model_table.py -- Merge bootstrap CIs into cross_model_table.csv.

Reads:
  research/figures/stats_overall.csv             (CIs for gpt-4o-mini)
  research/figures_gpt41mini/stats_overall.csv   (CIs for gpt-4.1-mini)
  research/figures/cross_model_table.csv         (point estimates)

Writes:
  research/figures/cross_model_table.csv         (overwritten with CI columns added)

The script is IDEMPOTENT: running it twice produces the same result. It also
writes a backup of the original file before overwriting, so a botched run can
be reverted with one command.

Usage:
    cd research
    python add_cis_to_cross_model_table.py
"""

import csv
import pathlib
import shutil
from datetime import datetime

HERE = pathlib.Path(__file__).parent
PRIMARY_STATS = HERE / "figures" / "stats_overall.csv"
CROSS_STATS = HERE / "figures_gpt41mini" / "stats_overall.csv"
TARGET_TABLE = HERE / "figures" / "cross_model_table.csv"
BACKUP_DIR = HERE / "figures" / "_backups"


def load_stats(path):
    """Load a stats_overall.csv into a dict keyed by (pipeline, judge_type)."""
    out = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            key = (row["pipeline"], row["judge"])  # judge is "strict" or "lenient"
            out[key] = {
                "mean": float(row["mean"]),
                "ci_lower": float(row["ci_lower"]),
                "ci_upper": float(row["ci_upper"]),
            }
    return out


def main():
    # Sanity: all three source files must exist
    for p in [PRIMARY_STATS, CROSS_STATS, TARGET_TABLE]:
        if not p.exists():
            raise FileNotFoundError(f"Missing required file: {p}")

    # Backup the target
    BACKUP_DIR.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"cross_model_table_pre_ci_{ts}.csv"
    shutil.copy2(TARGET_TABLE, backup_path)
    print(f"Backup written to: {backup_path}")

    # Load CI stats for both models
    primary_ci = load_stats(PRIMARY_STATS)
    cross_ci = load_stats(CROSS_STATS)
    print(f"Loaded {len(primary_ci)} stats rows for gpt-4o-mini")
    print(f"Loaded {len(cross_ci)} stats rows for gpt-4.1-mini")

    # Map: gen_model name in target table -> stats dict
    stats_for = {
        "gpt-4o-mini": primary_ci,
        "gpt-4.1-mini": cross_ci,
    }

    # Read the target table
    with open(TARGET_TABLE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        in_fieldnames = reader.fieldnames
        rows = list(reader)
    print(f"Read {len(rows)} rows from cross_model_table.csv")

    # Build the new column order: existing columns first, then 4 CI columns at the end
    new_columns = ["ci_lo_strict", "ci_hi_strict", "ci_lo_lenient", "ci_hi_lenient"]
    out_fieldnames = list(in_fieldnames)
    for c in new_columns:
        if c not in out_fieldnames:
            out_fieldnames.append(c)

    # Augment each row
    for row in rows:
        gm = row["gen_model"]
        pipe = row["pipeline"]
        if gm not in stats_for:
            raise ValueError(f"Unknown gen_model in cross_model_table.csv: {gm}")
        d = stats_for[gm]
        if (pipe, "strict") not in d or (pipe, "lenient") not in d:
            raise ValueError(f"No stats for ({gm}, {pipe}) in stats_overall files")
        row["ci_lo_strict"] = f"{d[(pipe, 'strict')]['ci_lower']:.4f}"
        row["ci_hi_strict"] = f"{d[(pipe, 'strict')]['ci_upper']:.4f}"
        row["ci_lo_lenient"] = f"{d[(pipe, 'lenient')]['ci_lower']:.4f}"
        row["ci_hi_lenient"] = f"{d[(pipe, 'lenient')]['ci_upper']:.4f}"

    # Write back
    with open(TARGET_TABLE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=out_fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {TARGET_TABLE}")
    print(f"Columns: {out_fieldnames}")
    print("Done.")


if __name__ == "__main__":
    main()
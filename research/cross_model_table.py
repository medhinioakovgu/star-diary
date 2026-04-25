"""
cross_model_table.py -- Summarise preservation rates across two generation models.

Reads two judgments CSVs (one per generation model), produces a comparison
table of overall preservation rates per (gen_model, pipeline, verdict_type).
Writes to research/figures/cross_model_table.csv.

Usage:
    cd research
    python cross_model_table.py
"""

import csv
import pathlib

HERE = pathlib.Path(__file__).parent
PRIMARY  = HERE / "data" / "judgments" / "judgments_weekly_magazine_openai-4o-mini.csv"
CROSS    = HERE / "data" / "judgments" / "gpt41mini" / "judgments_weekly_magazine_openai-4o-mini.csv"
OUT      = HERE / "figures" / "cross_model_table.csv"


def rate(rows, pipe, key):
    r = [x for x in rows if x["pipeline"] == pipe]
    if not r:
        return None, 0
    y = sum(1 for x in r if x[key] == "YES")
    return y / len(r), len(r)


def main():
    primary = list(csv.DictReader(open(PRIMARY, encoding="utf-8")))
    cross   = list(csv.DictReader(open(CROSS,    encoding="utf-8")))

    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["gen_model", "pipeline", "n",
                    "preservation_strict", "preservation_lenient"])
        for label, rows in [("gpt-4o-mini", primary), ("gpt-4.1-mini", cross)]:
            for pipe in ["neutral", "stylized", "decoupled"]:
                s, n = rate(rows, pipe, "verdict_strict")
                l, _ = rate(rows, pipe, "verdict_lenient")
                if s is not None:
                    w.writerow([label, pipe, n,
                                f"{s:.4f}", f"{l:.4f}"])

    print(f"Wrote {OUT}")
    print()

    # Pretty-print for sanity check
    primary = list(csv.DictReader(open(OUT, encoding="utf-8")))
    print(f"{'gen_model':<16} {'pipeline':<12} {'n':>5} {'strict':>8} {'lenient':>9}")
    print("-" * 56)
    for r in primary:
        print(f"{r['gen_model']:<16} {r['pipeline']:<12} "
              f"{r['n']:>5} {float(r['preservation_strict']):>8.3f} "
              f"{float(r['preservation_lenient']):>9.3f}")


if __name__ == "__main__":
    main()
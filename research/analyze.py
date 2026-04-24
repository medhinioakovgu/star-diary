"""
analyze.py -- Read the judgments CSV and produce the figures for the paper.

Figure 1 (HEADLINE): fact-decay-by-day-of-origin curves in the Day-7 weekly magazine.
    X-axis: day-of-origin (1..7)
    Y-axis: fraction of facts preserved (YES / all)
    Three lines: neutral, stylized, decoupled
    One figure for strict judge, one for lenient judge.

Figure 2: same decay curves but broken down by fact type (named_entity, quantitative,
    relational, emotional). 4-panel figure.

Figure 3: inter-judge agreement stats (printed to console, saved to a text file).

Also prints a summary table to the console and saves it as figures/summary_table.csv.

Usage:
    python analyze.py --judgments data/judgments/judgments_weekly_magazine_groq-llama-70b.csv
"""

import argparse
import csv
import pathlib
from collections import defaultdict


def load_judgments(path: pathlib.Path) -> list:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def preservation_rate(rows: list, verdict_key: str) -> float:
    """Fraction of rows where verdict == YES. UNCLEAR counts as NO (conservative)."""
    if not rows:
        return 0.0
    yes = sum(1 for r in rows if r[verdict_key] == "YES")
    return yes / len(rows)


def compute_decay_curve(rows: list, pipeline: str, verdict_key: str) -> dict:
    """For given pipeline, return {day_of_origin: preservation_rate}."""
    by_day = defaultdict(list)
    for r in rows:
        if r["pipeline"] == pipeline:
            by_day[int(r["fact_day"])].append(r)
    return {d: preservation_rate(by_day[d], verdict_key) for d in sorted(by_day)}


def cohens_kappa(rows: list) -> float:
    """Inter-judge agreement on the YES/NO/UNCLEAR verdict pair."""
    # Collapse UNCLEAR to NO for the kappa calculation (standard practice).
    def collapse(v):
        return "YES" if v == "YES" else "NO"
    a = [collapse(r["verdict_strict"]) for r in rows]
    b = [collapse(r["verdict_lenient"]) for r in rows]
    n = len(a)
    if n == 0:
        return float("nan")
    # Observed agreement
    po = sum(1 for x, y in zip(a, b) if x == y) / n
    # Expected agreement (chance)
    labels = {"YES", "NO"}
    pe = 0.0
    for lab in labels:
        pa = sum(1 for x in a if x == lab) / n
        pb = sum(1 for x in b if x == lab) / n
        pe += pa * pb
    if pe == 1.0:
        return 1.0
    return (po - pe) / (1 - pe)


def plot_decay_curves(rows: list, verdict_key: str, out_path: pathlib.Path, title: str):
    """Figure 1: decay curves by pipeline."""
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not installed, skipping plot. Run: pip install matplotlib")
        return

    pipelines = sorted({r["pipeline"] for r in rows})
    fig, ax = plt.subplots(figsize=(6, 4))
    for pipe in pipelines:
        curve = compute_decay_curve(rows, pipe, verdict_key)
        days = sorted(curve)
        rates = [curve[d] for d in days]
        ax.plot(days, rates, marker="o", label=pipe)
    ax.set_xlabel("Day-of-origin of fact (1 = earliest)")
    ax.set_ylabel("Fraction of facts preserved in Day-7 weekly magazine")
    ax.set_title(title)
    ax.set_ylim(0, 1.05)
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_path, dpi=200)
    print(f"  Saved {out_path}")


def plot_decay_by_type(rows: list, verdict_key: str, out_path: pathlib.Path, title: str):
    """Figure 2: 4-panel decay curves, one panel per fact type."""
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        return

    fact_types = ["named_entity", "quantitative", "relational", "emotional"]
    pipelines = sorted({r["pipeline"] for r in rows})
    fig, axes = plt.subplots(2, 2, figsize=(10, 7), sharex=True, sharey=True)
    for ax, ftype in zip(axes.flat, fact_types):
        subset = [r for r in rows if r["fact_type"] == ftype]
        for pipe in pipelines:
            curve = compute_decay_curve(subset, pipe, verdict_key)
            if not curve:
                continue
            days = sorted(curve)
            rates = [curve[d] for d in days]
            ax.plot(days, rates, marker="o", label=pipe)
        ax.set_title(f"Fact type: {ftype}")
        ax.set_ylim(0, 1.05)
        ax.grid(True, alpha=0.3)
    axes[1][0].set_xlabel("Day-of-origin")
    axes[1][1].set_xlabel("Day-of-origin")
    axes[0][0].set_ylabel("Preservation rate")
    axes[1][0].set_ylabel("Preservation rate")
    axes[0][0].legend(loc="lower left", fontsize=8)
    fig.suptitle(title)
    fig.tight_layout()
    fig.savefig(out_path, dpi=200)
    print(f"  Saved {out_path}")


def summary_table(rows: list, out_path: pathlib.Path):
    """Summary table: overall preservation rate per pipeline, both judges."""
    pipelines = sorted({r["pipeline"] for r in rows})
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["pipeline", "n_judgments", "preservation_strict", "preservation_lenient"])
        for pipe in pipelines:
            subset = [r for r in rows if r["pipeline"] == pipe]
            strict = preservation_rate(subset, "verdict_strict")
            lenient = preservation_rate(subset, "verdict_lenient")
            w.writerow([pipe, len(subset), f"{strict:.3f}", f"{lenient:.3f}"])
            print(f"  {pipe}: n={len(subset)}, strict={strict:.3f}, lenient={lenient:.3f}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--judgments", required=True,
                        help="Path to judgments CSV produced by judge.py.")
    parser.add_argument("--out", default="figures",
                        help="Output directory for figures and tables.")
    args = parser.parse_args()

    judgments_path = pathlib.Path(args.judgments)
    if not judgments_path.is_absolute():
        judgments_path = pathlib.Path(__file__).parent / judgments_path
    rows = load_judgments(judgments_path)
    print(f"Loaded {len(rows)} judgment rows from {judgments_path}")

    out_dir = pathlib.Path(__file__).parent / args.out
    out_dir.mkdir(parents=True, exist_ok=True)

    # Filter: only Day-7 artifact rows (weekly magazine). Judgments file may contain more.
    day7_rows = [r for r in rows if int(r["day_evaluated"]) == 7]
    print(f"  {len(day7_rows)} rows correspond to the Day-7 weekly magazine.")

    print("\n--- Summary table (Day-7 magazine) ---")
    summary_table(day7_rows, out_dir / "summary_table.csv")

    print("\n--- Inter-judge agreement ---")
    kappa = cohens_kappa(day7_rows)
    print(f"  Cohen's kappa (strict vs lenient): {kappa:.3f}")
    (out_dir / "interjudge_agreement.txt").write_text(
        f"Cohen's kappa (strict vs lenient): {kappa:.4f}\n"
        f"N judgments: {len(day7_rows)}\n"
    )

    print("\n--- Figure 1: decay curves (strict judge) ---")
    plot_decay_curves(day7_rows, "verdict_strict",
                      out_dir / "fig1_decay_strict.png",
                      "Fact preservation by day-of-origin (strict judge)")
    print("\n--- Figure 1b: decay curves (lenient judge) ---")
    plot_decay_curves(day7_rows, "verdict_lenient",
                      out_dir / "fig1_decay_lenient.png",
                      "Fact preservation by day-of-origin (lenient judge)")

    print("\n--- Figure 2: decay by fact type (strict judge) ---")
    plot_decay_by_type(day7_rows, "verdict_strict",
                       out_dir / "fig2_decay_by_type_strict.png",
                       "Fact preservation by day-of-origin and fact type (strict)")

    print(f"\nAll outputs in {out_dir}")


if __name__ == "__main__":
    main()

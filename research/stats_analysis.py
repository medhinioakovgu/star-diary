"""
stats_analysis.py -- Bootstrap confidence intervals and Wilcoxon signed-rank tests
for fact-preservation rates in the Star-Diary paper.

Produces four output files (all in research/figures/ by default):
  stats_overall.csv        -- per-pipeline mean preservation + 95% CI (bootstrap)
  stats_decay_by_day.csv   -- per-(pipeline, fact_day) mean preservation + 95% CI
  stats_paired_tests.csv   -- pairwise Wilcoxon signed-rank p-values (per-week rates)
  fig1_decay_strict_with_ci.png -- Figure 1 re-drawn with shaded 95% CI bands

The Wilcoxon test operates on per-week preservation rates (one observation per week
per pipeline), giving 15 paired observations per comparison. This is the correct
unit of analysis: weeks are the experimental unit, not individual facts.

Bootstrap uses 10,000 resamples with replacement over the 15 weeks. The reported
CI is the 2.5th–97.5th percentile of the bootstrap distribution of mean preservation.

Usage:
    cd research
    python stats_analysis.py                      # uses default paths
    python stats_analysis.py --judgments data/judgments/gpt41mini/judgments_weekly_magazine_openai-4o-mini.csv --out figures_gpt41mini
"""

import argparse
import csv
import pathlib
import random
import math
from collections import defaultdict


# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------

def bootstrap_ci(values, n_boot=10_000, ci=0.95, seed=42):
    """Return (mean, lower, upper) via percentile bootstrap."""
    rng = random.Random(seed)
    n = len(values)
    if n == 0:
        return float("nan"), float("nan"), float("nan")
    boot_means = []
    for _ in range(n_boot):
        sample = [rng.choice(values) for _ in range(n)]
        boot_means.append(sum(sample) / n)
    boot_means.sort()
    alpha = 1 - ci
    lo_idx = int(math.floor(alpha / 2 * n_boot))
    hi_idx = int(math.ceil((1 - alpha / 2) * n_boot)) - 1
    mean = sum(values) / n
    return mean, boot_means[lo_idx], boot_means[hi_idx]


# ---------------------------------------------------------------------------
# Wilcoxon signed-rank test (pure Python, no scipy dependency)
# ---------------------------------------------------------------------------

def wilcoxon_signed_rank(x, y):
    """
    Two-sided Wilcoxon signed-rank test on paired samples x, y.
    Returns (W_statistic, p_value_approx).
    Uses normal approximation (valid for n >= 10).
    """
    diffs = [xi - yi for xi, yi in zip(x, y) if xi != yi]
    n = len(diffs)
    if n == 0:
        return 0.0, 1.0

    abs_diffs = sorted(enumerate(abs(d) for d in diffs), key=lambda t: t[1])

    # Assign ranks with tie-averaging
    ranks = [0.0] * len(diffs)
    i = 0
    while i < len(abs_diffs):
        j = i
        while j < len(abs_diffs) and abs_diffs[j][1] == abs_diffs[i][1]:
            j += 1
        avg_rank = (i + 1 + j) / 2.0  # 1-indexed average
        for k in range(i, j):
            ranks[abs_diffs[k][0]] = avg_rank
        i = j

    W_plus  = sum(r for d, r in zip(diffs, ranks) if d > 0)
    W_minus = sum(r for d, r in zip(diffs, ranks) if d < 0)
    W = min(W_plus, W_minus)

    # Normal approximation
    mean_W  = n * (n + 1) / 4.0
    var_W   = n * (n + 1) * (2 * n + 1) / 24.0
    if var_W == 0:
        return W, 1.0
    z = (W - mean_W) / math.sqrt(var_W)

    # Two-tailed p-value from normal CDF (Abramowitz & Stegun approximation)
    p = 2 * _normal_sf(abs(z))
    return W, p


def _normal_sf(z):
    """Survival function (1 - CDF) of standard normal, for z >= 0."""
    # Approximation accurate to ~1e-7 (Abramowitz & Stegun 26.2.17)
    t = 1.0 / (1.0 + 0.2316419 * z)
    poly = t * (0.319381530
              + t * (-0.356563782
              + t * (1.781477937
              + t * (-1.821255978
              + t * 1.330274429))))
    return poly * math.exp(-0.5 * z * z) / math.sqrt(2 * math.pi)


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_judgments(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def per_week_rates(rows, pipeline, verdict_col="verdict_strict"):
    """Return list of per-week preservation rates for one pipeline."""
    by_week = defaultdict(list)
    for r in rows:
        if r["pipeline"] == pipeline:
            by_week[r["week_id"]].append(r[verdict_col] == "YES")
    return [sum(v) / len(v) for v in by_week.values() if v]


def per_week_day_rates(rows, pipeline, verdict_col="verdict_strict"):
    """Return dict: fact_day -> list of per-week preservation rates."""
    by_day_week = defaultdict(lambda: defaultdict(list))
    for r in rows:
        if r["pipeline"] == pipeline:
            by_day_week[r["fact_day"]][r["week_id"]].append(r[verdict_col] == "YES")
    result = {}
    for day, weeks in by_day_week.items():
        result[day] = [sum(v) / len(v) for v in weeks.values() if v]
    return result


# ---------------------------------------------------------------------------
# Figure 1 with CI bands (matplotlib)
# ---------------------------------------------------------------------------

def plot_with_ci(rows, out_path):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches
    except ImportError:
        print("  matplotlib not available — skipping CI figure")
        return

    COLORS    = {"neutral": "#0072B2", "stylized": "#D55E00", "decoupled": "#009E73"}
    LINESTYLE = {"neutral": "-",        "stylized": "--",      "decoupled": ":"}
    MARKERS   = {"neutral": "o",        "stylized": "s",       "decoupled": "^"}
    LABELS    = {"neutral": "Neutral",  "stylized": "Stylized","decoupled": "Decoupled"}

    fig, ax = plt.subplots(figsize=(3.5, 2.8))

    days = [str(d) for d in range(1, 8)]
    for pipe in ["neutral", "stylized", "decoupled"]:
        by_day = per_week_day_rates(rows, pipe)
        means, los, his = [], [], []
        for day in days:
            vals = by_day.get(day, [])
            m, lo, hi = bootstrap_ci(vals)
            means.append(m); los.append(lo); his.append(hi)

        ax.plot(days, means,
                color=COLORS[pipe], linestyle=LINESTYLE[pipe],
                marker=MARKERS[pipe], markersize=5, linewidth=1.5,
                label=LABELS[pipe])
        ax.fill_between(days, los, his,
                         color=COLORS[pipe], alpha=0.15)

    ax.set_xlabel("Day fact was introduced", fontsize=9)
    ax.set_ylabel("Preservation rate (strict)", fontsize=9)
    ax.set_ylim(-0.05, 1.05)
    ax.legend(fontsize=8, loc="lower right")
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    ax.tick_params(labelsize=8)
    fig.tight_layout()
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {out_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--judgments",
                        default="data/judgments/judgments_weekly_magazine_openai-4o-mini.csv")
    parser.add_argument("--out", default="figures",
                        help="Output directory for stats CSVs and figure.")
    parser.add_argument("--n_boot", type=int, default=10_000)
    args = parser.parse_args()

    rows = load_judgments(pathlib.Path(__file__).parent / args.judgments)
    out_dir = pathlib.Path(__file__).parent / args.out
    out_dir.mkdir(parents=True, exist_ok=True)

    pipelines = ["neutral", "stylized", "decoupled"]

    # ------------------------------------------------------------------
    # 1. Overall preservation rates with bootstrap CI
    # ------------------------------------------------------------------
    print("Computing overall preservation rates...")
    overall_rows = []
    for pipe in pipelines:
        for verdict_col, label in [("verdict_strict", "strict"), ("verdict_lenient", "lenient")]:
            week_rates = per_week_rates(rows, pipe, verdict_col)
            mean, lo, hi = bootstrap_ci(week_rates, n_boot=args.n_boot)
            overall_rows.append({
                "pipeline": pipe,
                "judge": label,
                "n_weeks": len(week_rates),
                "mean": f"{mean:.4f}",
                "ci_lower": f"{lo:.4f}",
                "ci_upper": f"{hi:.4f}",
            })
            print(f"  {pipe} ({label}): {mean:.3f} [{lo:.3f}, {hi:.3f}]")

    out_overall = out_dir / "stats_overall.csv"
    with open(out_overall, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["pipeline","judge","n_weeks","mean","ci_lower","ci_upper"])
        w.writeheader(); w.writerows(overall_rows)
    print(f"  Saved: {out_overall}\n")

    # ------------------------------------------------------------------
    # 2. Decay by day with bootstrap CI
    # ------------------------------------------------------------------
    print("Computing per-day preservation rates...")
    day_rows = []
    for pipe in pipelines:
        by_day = per_week_day_rates(rows, pipe, "verdict_strict")
        for day in sorted(by_day.keys(), key=int):
            vals = by_day[day]
            mean, lo, hi = bootstrap_ci(vals, n_boot=args.n_boot)
            day_rows.append({
                "pipeline": pipe,
                "fact_day": day,
                "n_weeks": len(vals),
                "mean": f"{mean:.4f}",
                "ci_lower": f"{lo:.4f}",
                "ci_upper": f"{hi:.4f}",
            })

    out_day = out_dir / "stats_decay_by_day.csv"
    with open(out_day, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["pipeline","fact_day","n_weeks","mean","ci_lower","ci_upper"])
        w.writeheader(); w.writerows(day_rows)
    print(f"  Saved: {out_day}\n")

    # ------------------------------------------------------------------
    # 3. Pairwise Wilcoxon signed-rank tests (per-week rates)
    # ------------------------------------------------------------------
    print("Running paired Wilcoxon signed-rank tests...")
    pairs = [
        ("neutral",   "stylized"),
        ("neutral",   "decoupled"),
        ("decoupled", "stylized"),
    ]
    test_rows = []
    for pipe_a, pipe_b in pairs:
        for verdict_col, label in [("verdict_strict", "strict"), ("verdict_lenient", "lenient")]:
            rates_a = per_week_rates(rows, pipe_a, verdict_col)
            rates_b = per_week_rates(rows, pipe_b, verdict_col)
            # Align by week (both should have same 15 weeks; zip is safe here)
            W, p = wilcoxon_signed_rank(rates_a, rates_b)
            sig = "***" if p < 0.001 else ("**" if p < 0.01 else ("*" if p < 0.05 else "ns"))
            test_rows.append({
                "comparison": f"{pipe_a} vs {pipe_b}",
                "judge": label,
                "W_statistic": f"{W:.1f}",
                "p_value": f"{p:.4f}",
                "significance": sig,
            })
            print(f"  {pipe_a} vs {pipe_b} ({label}): W={W:.1f}, p={p:.4f} {sig}")

    out_tests = out_dir / "stats_paired_tests.csv"
    with open(out_tests, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["comparison","judge","W_statistic","p_value","significance"])
        w.writeheader(); w.writerows(test_rows)
    print(f"  Saved: {out_tests}\n")

    # ------------------------------------------------------------------
    # 4. Figure 1 with CI bands
    # ------------------------------------------------------------------
    print("Generating Figure 1 with confidence interval bands...")
    fig_path = out_dir / "fig1_decay_strict_with_ci.png"
    plot_with_ci(rows, fig_path)

    print("\nAll done. Files written:")
    for p in [out_overall, out_day, out_tests, fig_path]:
        print(f"  {p}")


if __name__ == "__main__":
    main()
"""
build_combined_figure.py — 2-panel cross-model decay figure for the paper.

Reads:
    research/figures/stats_decay_by_day.csv             (gpt-4o-mini)
    research/figures_gpt41mini/stats_decay_by_day.csv   (gpt-4.1-mini)

Writes:
    research/figures/fig_combined_decay_2panel.png

Both panels:
  - x-axis: fact day-of-origin (1..7)
  - y-axis: preservation rate (strict judge)
  - three lines (neutral, stylized, decoupled), each with a shaded 95% CI band
  - identical x and y axis ranges
  - same colours/markers across panels for cross-panel comparability

Re-run any time the underlying CSVs change. No CLI args.
"""

import csv
import pathlib
from collections import defaultdict

import matplotlib.pyplot as plt

BASE       = pathlib.Path(__file__).parent
CSV_4O     = BASE / "figures" / "stats_decay_by_day.csv"
CSV_41     = BASE / "figures_gpt41mini" / "stats_decay_by_day.csv"
OUT_PATH   = BASE / "figures" / "fig_combined_decay_2panel.png"

# Same colour mapping used in the existing single-panel figure.
PIPELINE_COLOR = {
    "neutral":   "#1f77b4",   # blue
    "stylized":  "#d62728",   # red
    "decoupled": "#2ca02c",   # green
}
PIPELINE_MARKER = {
    "neutral":   "o",
    "stylized":  "s",
    "decoupled": "^",
}
PIPELINE_ORDER = ["neutral", "stylized", "decoupled"]


def load_decay(path: pathlib.Path) -> dict:
    """Returns {pipeline: {'days': [...], 'mean': [...], 'lo': [...], 'hi': [...]}}"""
    by_pipe = defaultdict(lambda: {"days": [], "mean": [], "lo": [], "hi": []})
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            p = row["pipeline"]
            by_pipe[p]["days"].append(int(row["fact_day"]))
            by_pipe[p]["mean"].append(float(row["mean"]))
            by_pipe[p]["lo"].append(float(row["ci_lower"]))
            by_pipe[p]["hi"].append(float(row["ci_upper"]))
    # Sort each pipeline's data by day (CSV is usually already sorted, defensive)
    for p, d in by_pipe.items():
        order = sorted(range(len(d["days"])), key=lambda i: d["days"][i])
        d["days"] = [d["days"][i] for i in order]
        d["mean"] = [d["mean"][i] for i in order]
        d["lo"]   = [d["lo"][i]   for i in order]
        d["hi"]   = [d["hi"][i]   for i in order]
    return dict(by_pipe)


def plot_panel(ax, data: dict, title: str) -> None:
    for pipe in PIPELINE_ORDER:
        if pipe not in data:
            continue
        d = data[pipe]
        color  = PIPELINE_COLOR[pipe]
        marker = PIPELINE_MARKER[pipe]
        ax.plot(
            d["days"], d["mean"],
            color=color, marker=marker, markersize=6,
            linewidth=2, label=pipe,
        )
        ax.fill_between(d["days"], d["lo"], d["hi"], color=color, alpha=0.15)
    ax.set_title(title, fontsize=11)
    ax.set_xlabel("Fact day-of-origin", fontsize=10)
    ax.set_xticks(range(1, 8))
    ax.set_ylim(0.0, 1.05)
    ax.set_xlim(0.7, 7.3)
    ax.grid(True, linestyle="--", alpha=0.35)


def main() -> None:
    if not CSV_4O.exists():
        raise FileNotFoundError(f"Missing {CSV_4O}")
    if not CSV_41.exists():
        raise FileNotFoundError(f"Missing {CSV_41}")

    data_4o = load_decay(CSV_4O)
    data_41 = load_decay(CSV_41)

    fig, (ax_left, ax_right) = plt.subplots(1, 2, figsize=(11, 4.5), sharey=True)

    plot_panel(ax_left,  data_4o, "(a) gpt-4o-mini")
    plot_panel(ax_right, data_41, "(b) gpt-4.1-mini")

    ax_left.set_ylabel("Preservation rate (strict judge, 95% CI)", fontsize=10)

    # Single shared legend at the bottom rather than two duplicated ones
    handles, labels = ax_left.get_legend_handles_labels()
    fig.legend(
        handles, labels,
        loc="lower center", ncol=3,
        bbox_to_anchor=(0.5, -0.02),
        frameon=False, fontsize=10,
    )

    fig.suptitle("Day-of-origin fact preservation: cross-model comparison", fontsize=12, y=1.00)
    fig.tight_layout(rect=(0, 0.04, 1, 0.97))

    fig.savefig(OUT_PATH, dpi=200, bbox_inches="tight")
    print(f"Saved {OUT_PATH.relative_to(BASE.parent)}")
    print(f"  Panel A pipelines: {sorted(data_4o.keys())}")
    print(f"  Panel B pipelines: {sorted(data_41.keys())}")


if __name__ == "__main__":
    main()
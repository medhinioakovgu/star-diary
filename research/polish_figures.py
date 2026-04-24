"""
polish_figures.py
=================
Re-generates fig1 (strict + lenient) and fig2 from the judgments CSV with
publication-quality styling for ACM paper submission:

  - Colorblind-safe palette (Okabe-Ito / Wong 2011)
  - Distinct line styles (solid / dashed / dotted) for B&W printing
  - Font sizes readable at ACM single-column width (3.33 inches)
  - 300 DPI output
  - Overwrites existing figures in research/figures/

Run from inside research/:
    python polish_figures.py --judgments data/judgments/judgments_weekly_magazine_openai-4o-mini.csv

To preview without overwriting:
    python polish_figures.py --judgments data/judgments/judgments_weekly_magazine_openai-4o-mini.csv --preview
"""

from __future__ import annotations

import argparse
import csv
import pathlib
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np

# ── PATHS ─────────────────────────────────────────────────────────────────────
BASE        = pathlib.Path(__file__).parent
FIGURES_DIR = BASE / "figures"

# ── STYLE ─────────────────────────────────────────────────────────────────────
# Okabe-Ito colorblind-safe palette (Wong 2011, doi:10.1038/nmeth.1618)
# Assigned: neutral=blue, stylized=vermillion, decoupled=bluish-green
PIPELINE_STYLE = {
    "neutral":   {"color": "#0072B2", "linestyle": "-",  "marker": "o", "label": "neutral"},
    "stylized":  {"color": "#D55E00", "linestyle": "--", "marker": "s", "label": "stylized"},
    "decoupled": {"color": "#009E73", "linestyle": ":",  "marker": "^", "label": "decoupled"},
}
PIPELINE_ORDER = ["neutral", "stylized", "decoupled"]

# ACM column widths (inches)
SINGLE_COL_W = 3.5   # slightly wider than 3.33 to give breathing room
DOUBLE_COL_W = 7.0

# Font sizes
TITLE_SIZE  = 10
LABEL_SIZE  = 9
TICK_SIZE   = 8
LEGEND_SIZE = 8
DPI         = 300


# ── DATA LOADING ──────────────────────────────────────────────────────────────
def load_judgments(csv_path: pathlib.Path) -> list[dict]:
    with open(csv_path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def preservation_rate(rows: list[dict], verdict_col: str) -> float:
    """Fraction of YES verdicts (UNCLEAR treated as NO)."""
    if not rows:
        return float("nan")
    return sum(1 for r in rows if r[verdict_col].strip().upper() == "YES") / len(rows)


def decay_by_day(
    rows: list[dict],
    verdict_col: str,
) -> dict[str, dict[int, float]]:
    """
    Returns {pipeline: {day: preservation_rate}} for days 1-7.
    Only includes days with at least 1 judgment.
    """
    grouped: dict[str, dict[int, list[dict]]] = defaultdict(lambda: defaultdict(list))
    for r in rows:
        grouped[r["pipeline"]][int(r["fact_day"])].append(r)

    result = {}
    for pipeline in PIPELINE_ORDER:
        result[pipeline] = {}
        for day in range(1, 8):
            day_rows = grouped[pipeline].get(day, [])
            if day_rows:
                result[pipeline][day] = preservation_rate(day_rows, verdict_col)
    return result


def decay_by_day_and_type(
    rows: list[dict],
    verdict_col: str,
    fact_types: list[str],
) -> dict[str, dict[str, dict[int, float]]]:
    """
    Returns {fact_type: {pipeline: {day: rate}}}.
    """
    result = {}
    for ft in fact_types:
        ft_rows = [r for r in rows if r["fact_type"] == ft]
        result[ft] = decay_by_day(ft_rows, verdict_col)
    return result


# ── SHARED PLOT HELPERS ───────────────────────────────────────────────────────
def _apply_common_axes(ax, title: str, xlabel: bool = True, ylabel: bool = True):
    ax.set_xlim(0.7, 7.3)
    ax.set_ylim(-0.05, 1.08)
    ax.set_xticks(range(1, 8))
    ax.set_yticks([0, 0.2, 0.4, 0.6, 0.8, 1.0])
    ax.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=1.0, decimals=0))
    ax.tick_params(labelsize=TICK_SIZE)
    ax.set_title(title, fontsize=TITLE_SIZE, pad=4)
    ax.grid(True, color="0.85", linewidth=0.6, zorder=0)
    ax.set_axisbelow(True)
    if xlabel:
        ax.set_xlabel("Day-of-origin of fact  (1 = earliest)", fontsize=LABEL_SIZE)
    if ylabel:
        ax.set_ylabel("Facts preserved in\nDay-7 magazine", fontsize=LABEL_SIZE)


def _plot_decay_lines(ax, decay: dict[str, dict[int, float]], legend: bool = True):
    for pipeline in PIPELINE_ORDER:
        if pipeline not in decay:
            continue
        days  = sorted(decay[pipeline].keys())
        rates = [decay[pipeline][d] for d in days]
        s = PIPELINE_STYLE[pipeline]
        ax.plot(
            days, rates,
            color=s["color"],
            linestyle=s["linestyle"],
            marker=s["marker"],
            markersize=5,
            linewidth=1.6,
            label=s["label"],
            zorder=3,
        )
    if legend:
        ax.legend(
            fontsize=LEGEND_SIZE,
            loc="lower right",
            framealpha=0.9,
            edgecolor="0.7",
            handlelength=2.5,
        )


# ── FIGURE 1 — STRICT ─────────────────────────────────────────────────────────
def make_fig1_strict(rows: list[dict], out_path: pathlib.Path) -> None:
    decay = decay_by_day(rows, "verdict_strict")

    fig, ax = plt.subplots(figsize=(SINGLE_COL_W, 2.8))
    _plot_decay_lines(ax, decay, legend=True)
    _apply_common_axes(ax, "Fact preservation by day-of-origin (strict judge)")

    fig.tight_layout(pad=0.5)
    fig.savefig(out_path, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {out_path}")


# ── FIGURE 1b — LENIENT ───────────────────────────────────────────────────────
def make_fig1_lenient(rows: list[dict], out_path: pathlib.Path) -> None:
    decay = decay_by_day(rows, "verdict_lenient")

    fig, ax = plt.subplots(figsize=(SINGLE_COL_W, 2.8))
    _plot_decay_lines(ax, decay, legend=True)
    _apply_common_axes(ax, "Fact preservation by day-of-origin (lenient judge)")

    fig.tight_layout(pad=0.5)
    fig.savefig(out_path, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {out_path}")


# ── FIGURE 2 — BY FACT TYPE ────────────────────────────────────────────────────
FACT_TYPE_LABELS = {
    "named_entity": "Named entity",
    "quantitative": "Quantitative",
    "relational":   "Relational",
    "emotional":    "Emotional",
}
FACT_TYPE_ORDER = ["named_entity", "quantitative", "relational", "emotional"]


def make_fig2(rows: list[dict], out_path: pathlib.Path) -> None:
    by_type = decay_by_day_and_type(rows, "verdict_strict", FACT_TYPE_ORDER)

    fig, axes = plt.subplots(2, 2, figsize=(DOUBLE_COL_W, 4.8), sharey=True, sharex=True)
    axes_flat = axes.flatten()

    for i, ft in enumerate(FACT_TYPE_ORDER):
        ax = axes_flat[i]
        decay = by_type.get(ft, {})
        show_legend = (i == 0)
        _plot_decay_lines(ax, decay, legend=show_legend)
        _apply_common_axes(
            ax,
            title=FACT_TYPE_LABELS[ft],
            xlabel=(i >= 2),   # only bottom row
            ylabel=(i % 2 == 0),  # only left column
        )

    fig.suptitle(
        "Fact preservation by day-of-origin and fact type (strict judge)",
        fontsize=TITLE_SIZE + 1,
        y=1.01,
    )

    # Shared legend below the suptitle, pulling from the first axis
    handles, labels = axes_flat[0].get_legend_handles_labels()
    axes_flat[0].get_legend().remove()
    fig.legend(
        handles, labels,
        loc="upper right",
        bbox_to_anchor=(1.0, 1.0),
        fontsize=LEGEND_SIZE,
        framealpha=0.9,
        edgecolor="0.7",
        handlelength=2.5,
        ncol=1,
    )

    fig.tight_layout(pad=0.6, h_pad=1.2, w_pad=0.8)
    fig.savefig(out_path, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {out_path}")


# ── MAIN ─────────────────────────────────────────────────────────────────────
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Re-generate polished figures for the paper."
    )
    parser.add_argument(
        "--judgments",
        type=pathlib.Path,
        default=BASE / "data" / "judgments" / "judgments_weekly_magazine_openai-4o-mini.csv",
        help="Path to the judgments CSV.",
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Save to figures/polished_* instead of overwriting originals.",
    )
    args = parser.parse_args()

    if not args.judgments.exists():
        print(f"Error: judgments file not found at {args.judgments}")
        return

    FIGURES_DIR.mkdir(exist_ok=True)
    prefix = "polished_" if args.preview else ""

    print(f"Loading judgments from {args.judgments}...")
    rows = load_judgments(args.judgments)
    print(f"  {len(rows)} rows loaded.\n")

    print("Generating figures...")
    make_fig1_strict(rows,   FIGURES_DIR / f"{prefix}fig1_decay_strict.png")
    make_fig1_lenient(rows,  FIGURES_DIR / f"{prefix}fig1_decay_lenient.png")
    make_fig2(rows,          FIGURES_DIR / f"{prefix}fig2_decay_by_type_strict.png")

    print(f"\nDone. All figures in {FIGURES_DIR}/")
    if args.preview:
        print("Preview mode: originals were NOT overwritten.")
        print("If the preview looks good, re-run without --preview to finalize.")


if __name__ == "__main__":
    main()
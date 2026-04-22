"""
spot_check.py -- Human validation of LLM judge verdicts.

Randomly samples rows from the judgments CSV, groups them by magazine so the
reviewer only has to read each magazine once, then asks YES / NO for each fact
WITHOUT showing the automated verdict (to avoid anchoring bias).

After all ratings are submitted, the app computes and displays:
  - Human vs. strict-judge agreement (%)
  - Human vs. lenient-judge agreement (%)
  - Cohen's kappa for both comparisons

Results saved to:  data/judgments/human_spotcheck.csv

Usage:
    cd research/
    streamlit run spot_check.py

Config (sidebar):
    - Reviewer name    (written to CSV so teammates' runs can be merged)
    - N items to rate  (default 50, split evenly across teammates)
    - Random seed      (default 42; keep fixed so all teammates draw from the same pool)
"""

from __future__ import annotations

import csv
import json
import pathlib
import random
from collections import defaultdict
from datetime import datetime

import streamlit as st

# ── PATHS (relative to research/) ────────────────────────────────────────────
BASE          = pathlib.Path(__file__).parent
JUDGMENTS_DIR = BASE / "data" / "judgments"
RESULTS_DIR   = BASE / "data" / "results"
SPOTCHECK_CSV = JUDGMENTS_DIR / "human_spotcheck.csv"

SPOTCHECK_FIELDS = [
    "reviewer", "timestamp",
    "week_id", "pipeline", "gen_model",
    "fact_id", "fact_day", "fact_type", "fact_text",
    "human_verdict",            # YES / NO
    "verdict_strict",           # from judge (for agreement calc, not shown during rating)
    "verdict_lenient",
]

PIPELINE_COLORS = {"neutral": "🔵", "stylized": "🔴", "decoupled": "🟢"}


# ── DATA LOADING ─────────────────────────────────────────────────────────────
@st.cache_data
def find_judgments_csv() -> pathlib.Path | None:
    """Return the most recently modified judgments CSV, or None if none exist."""
    candidates = list(JUDGMENTS_DIR.glob("judgments_weekly_magazine_*.csv"))
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)


@st.cache_data
def load_rows(csv_path: str) -> list[dict]:
    with open(csv_path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


@st.cache_data
def load_magazine(week_id: int, pipeline: str, gen_model: str) -> str:
    """Load weekly_magazine text from Akshat's result files."""
    path = RESULTS_DIR / f"week_{week_id:02d}" / gen_model / f"{pipeline}.json"
    if not path.exists():
        return f"[Result file not found: {path}]"
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("weekly_magazine", "[weekly_magazine key missing]")


def sample_rows(all_rows: list[dict], n: int, seed: int) -> list[dict]:
    """
    Sample n rows stratified by pipeline (equal representation).
    Uses a fixed seed for reproducibility — all teammates draw from the same pool.
    """
    rng = random.Random(seed)
    by_pipeline: dict[str, list[dict]] = defaultdict(list)
    for r in all_rows:
        by_pipeline[r["pipeline"]].append(r)

    pipelines = sorted(by_pipeline)
    per_pipeline = max(1, n // len(pipelines))
    sampled: list[dict] = []
    for pipe in pipelines:
        pool = by_pipeline[pipe]
        rng.shuffle(pool)
        sampled.extend(pool[:per_pipeline])

    # Top up to exactly n if rounding left us short
    remaining = [r for r in all_rows if r not in sampled]
    rng.shuffle(remaining)
    sampled.extend(remaining[: n - len(sampled)])
    return sampled[:n]


def group_by_magazine(rows: list[dict]) -> list[tuple[tuple, list[dict]]]:
    """
    Group rows by (week_id, pipeline, gen_model) so the reviewer reads each
    magazine once and rates all facts from that magazine together.
    Returns a sorted list of (key_tuple, [rows]) pairs.
    """
    groups: dict[tuple, list[dict]] = defaultdict(list)
    for r in rows:
        key = (int(r["week_id"]), r["pipeline"], r["gen_model"])
        groups[key].append(r)
    return sorted(groups.items())


# ── RESULTS SAVING ────────────────────────────────────────────────────────────
def save_answer(reviewer: str, row: dict, human_verdict: str) -> None:
    JUDGMENTS_DIR.mkdir(parents=True, exist_ok=True)
    write_header = not SPOTCHECK_CSV.exists()
    with open(SPOTCHECK_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=SPOTCHECK_FIELDS)
        if write_header:
            writer.writeheader()
        writer.writerow({
            "reviewer":       reviewer,
            "timestamp":      datetime.utcnow().isoformat(),
            "week_id":        row["week_id"],
            "pipeline":       row["pipeline"],
            "gen_model":      row["gen_model"],
            "fact_id":        row["fact_id"],
            "fact_day":       row["fact_day"],
            "fact_type":      row["fact_type"],
            "fact_text":      row["fact_text"],
            "human_verdict":  human_verdict,
            "verdict_strict": row["verdict_strict"],
            "verdict_lenient":row["verdict_lenient"],
        })


# ── AGREEMENT STATS ───────────────────────────────────────────────────────────
def cohens_kappa(a_list: list[str], b_list: list[str]) -> float:
    def collapse(v: str) -> str:
        return "YES" if v == "YES" else "NO"

    a = [collapse(x) for x in a_list]
    b = [collapse(x) for x in b_list]
    n = len(a)
    if n == 0:
        return float("nan")
    po = sum(1 for x, y in zip(a, b) if x == y) / n
    pe = sum(
        (sum(1 for x in a if x == lab) / n) * (sum(1 for x in b if x == lab) / n)
        for lab in {"YES", "NO"}
    )
    return (po - pe) / (1 - pe) if pe < 1.0 else 1.0


def compute_agreement(completed: list[dict]) -> dict:
    human    = [r["human_verdict"]  for r in completed]
    strict   = [r["verdict_strict"] for r in completed]
    lenient  = [r["verdict_lenient"]for r in completed]

    def pct_agree(a, b):
        pairs = [(x, "YES" if y == "YES" else "NO") for x, y in zip(a, b)]
        agreed = sum(1 for x, y in pairs if x == y)
        return agreed / len(pairs) * 100 if pairs else 0

    return {
        "n":                   len(completed),
        "agree_pct_strict":    pct_agree(human, strict),
        "agree_pct_lenient":   pct_agree(human, lenient),
        "kappa_strict":        cohens_kappa(human, strict),
        "kappa_lenient":       cohens_kappa(human, lenient),
    }


# ── SESSION INIT ──────────────────────────────────────────────────────────────
def init_session(rows: list[dict]) -> None:
    if "groups" not in st.session_state:
        st.session_state.groups        = group_by_magazine(rows)
        st.session_state.group_idx     = 0
        st.session_state.fact_idx      = 0
        st.session_state.completed     = []   # list of answered row dicts
        st.session_state.screen        = "rating"  # "rating" | "done"


# ── SCREENS ───────────────────────────────────────────────────────────────────
def screen_rating(reviewer: str, total: int) -> None:
    groups   = st.session_state.groups
    g_idx    = st.session_state.group_idx
    f_idx    = st.session_state.fact_idx
    done_n   = len(st.session_state.completed)

    if g_idx >= len(groups):
        st.session_state.screen = "done"
        st.rerun()
        return

    (week_id, pipeline, gen_model), facts_in_group = groups[g_idx]
    pipe_icon = PIPELINE_COLORS.get(pipeline, "⬜")

    # ── Progress ─────────────────────────────────────────────────────────────
    progress_frac = done_n / total if total > 0 else 0
    st.progress(progress_frac,
                text=f"Rated {done_n} / {total} facts  |  "
                     f"Group {g_idx + 1} / {len(groups)}")

    st.title("🔍 Human Spot-Check")
    st.caption(
        "Rate whether each fact is preserved in the summary — "
        "**do not** look at the automated verdicts yet."
    )

    # ── Magazine panel ───────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown(
        f"### {pipe_icon} Week {week_id} — **{pipeline}** pipeline  "
        f"<span style='color:grey;font-size:0.85em'>({gen_model})</span>",
        unsafe_allow_html=True,
    )

    with st.expander("📰 Weekly Magazine (click to expand — read this first)", expanded=True):
        magazine = load_magazine(week_id, pipeline, gen_model)
        st.markdown(magazine)

    # ── Current fact ─────────────────────────────────────────────────────────
    if f_idx >= len(facts_in_group):
        # Move to next group
        st.session_state.group_idx += 1
        st.session_state.fact_idx   = 0
        st.rerun()
        return

    row = facts_in_group[f_idx]
    remaining_in_group = len(facts_in_group) - f_idx

    st.markdown("---")
    st.markdown(
        f"**Fact {f_idx + 1} of {len(facts_in_group)} in this group** "
        f"&nbsp;·&nbsp; Day {row['fact_day']} &nbsp;·&nbsp; `{row['fact_type']}`"
    )
    st.info(f"**Fact:** {row['fact_text']}")

    st.markdown(
        "**Is this fact preserved in the magazine above?**  \n"
        "*(preserved = explicitly stated or clearly paraphrased — not just vaguely implied)*"
    )

    col_yes, col_no, col_skip = st.columns([1, 1, 2])
    with col_yes:
        if st.button("✅ YES", use_container_width=True, type="primary"):
            st.session_state.completed.append({**row, "human_verdict": "YES"})
            save_answer(reviewer, row, "YES")
            st.session_state.fact_idx += 1
            if done_n + 1 >= total:
                st.session_state.screen = "done"
            st.rerun()
    with col_no:
        if st.button("❌ NO", use_container_width=True):
            st.session_state.completed.append({**row, "human_verdict": "NO"})
            save_answer(reviewer, row, "NO")
            st.session_state.fact_idx += 1
            if done_n + 1 >= total:
                st.session_state.screen = "done"
            st.rerun()
    with col_skip:
        if st.button("⏭ Skip (unclear)", use_container_width=True):
            # Skip: don't record, just advance
            st.session_state.fact_idx += 1
            st.rerun()

    st.caption(
        f"{remaining_in_group - 1} more fact(s) in this group after this one. "
        "You can re-read the magazine above at any time."
    )


def screen_done() -> None:
    st.balloons()
    st.title("✅ Rating Complete")
    st.success(f"Saved to `{SPOTCHECK_CSV}`")

    completed = st.session_state.completed
    if len(completed) < 2:
        st.warning("Too few ratings to compute agreement statistics.")
        return

    stats = compute_agreement(completed)
    st.markdown("---")
    st.subheader("📊 Agreement with LLM Judge")

    col1, col2 = st.columns(2)
    with col1:
        st.metric("vs. Strict Judge",
                  f"{stats['agree_pct_strict']:.1f}% agree",
                  f"κ = {stats['kappa_strict']:.3f}")
    with col2:
        st.metric("vs. Lenient Judge",
                  f"{stats['agree_pct_lenient']:.1f}% agree",
                  f"κ = {stats['kappa_lenient']:.3f}")

    st.markdown(f"N rated: **{stats['n']}**")
    st.markdown("""
**Interpreting κ (Cohen's kappa):**
- κ > 0.80 → near-perfect agreement ✅
- 0.60–0.80 → substantial agreement ✅
- 0.40–0.60 → moderate agreement ⚠️
- < 0.40 → weak agreement — flag as limitation ❌
""")

    st.markdown("---")
    st.markdown(
        "**Share these numbers in the team chat** so Ritwika can add them to "
        "the methodology appendix. Also paste the full CSV path."
    )
    st.code(str(SPOTCHECK_CSV))


# ── MAIN ─────────────────────────────────────────────────────────────────────
def main() -> None:
    st.set_page_config(
        page_title="Human Spot-Check | Star-Diary",
        page_icon="🔍",
        layout="wide",
    )

    # ── Sidebar config ────────────────────────────────────────────────────────
    with st.sidebar:
        st.title("⚙️ Configuration")
        reviewer = st.text_input(
            "Your name (used in CSV)",
            placeholder="e.g. Medhini",
        ).strip()
        n_items = st.number_input(
            "Items to rate (total pool = 50, split 3 ways ≈ 17 each)",
            min_value=5, max_value=100, value=17, step=1,
        )
        seed = st.number_input("Random seed (keep at 42 for all reviewers)", value=42, step=1)
        st.markdown("---")
        st.markdown(
            "**Do not** change the seed after you start — "
            "all teammates must draw from the same 50-item pool."
        )

    if not reviewer:
        st.info("👈 Enter your name in the sidebar to begin.")
        return

    # ── Load data ─────────────────────────────────────────────────────────────
    csv_path = find_judgments_csv()
    if csv_path is None:
        st.error(
            "No judgments CSV found in `data/judgments/`. "
            "Run `python judge.py --artifact weekly_magazine` first."
        )
        return

    all_rows  = load_rows(str(csv_path))
    pool      = sample_rows(all_rows, 50, int(seed))   # fixed 50-item pool
    my_sample = pool[: int(n_items)]                    # each reviewer takes their slice

    init_session(my_sample)

    if st.session_state.screen == "done":
        screen_done()
    else:
        screen_rating(reviewer, total=int(n_items))


if __name__ == "__main__":
    main()
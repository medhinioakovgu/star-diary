"""
analyze_spotcheck.py -- Compute human-LLM agreement from the spot-check CSV.

The spot-check CSV (human_spotcheck.csv) already contains the LLM verdicts
(verdict_strict, verdict_lenient) pre-filled by the Streamlit app, so this
script does not need to look up the main judgments CSV.

Reports:
  - Items rated by all three reviewers (expected: 17)
  - Human-consensus verdict per item (2-of-3 majority vote)
  - Agreement between human consensus and strict LLM judge (% and kappa)
  - Agreement between human consensus and lenient LLM judge (% and kappa)
  - Pairwise Cohen's kappa among the three human reviewers
  - Any items where human consensus disagrees with either judge (for inspection)

Output: research/figures/human_validation.txt

Usage:
    cd research
    python analyze_spotcheck.py
"""

import csv
import pathlib
from collections import defaultdict, Counter

HERE = pathlib.Path(__file__).parent
SPOTCHECK_CSV = HERE / "data" / "judgments" / "human_spotcheck.csv"
OUT_TXT = HERE / "figures" / "human_validation.txt"

RATERS = ["Medhini", "Ritwika", "Akshat"]


def load_csv(p):
    with open(p, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def cohens_kappa(labels_a, labels_b):
    """Binary kappa over YES/NO labels."""
    n = len(labels_a)
    if n == 0:
        return float("nan")
    po = sum(1 for a, b in zip(labels_a, labels_b) if a == b) / n
    pe = 0.0
    for lab in ("YES", "NO"):
        pa = sum(1 for x in labels_a if x == lab) / n
        pb = sum(1 for x in labels_b if x == lab) / n
        pe += pa * pb
    if pe >= 1.0:
        return 1.0
    return (po - pe) / (1 - pe)


def main():
    spot = load_csv(SPOTCHECK_CSV)

    # ------------------------------------------------------------------
    # 1. Group rows by item key; each item has one row per reviewer
    # ------------------------------------------------------------------
    items = defaultdict(dict)  # key -> {reviewer -> row}
    for r in spot:
        key = (r["week_id"], r["pipeline"], r["fact_id"])
        items[key][r["reviewer"]] = r

    # Only items rated by all three reviewers
    complete = {k: v for k, v in items.items() if len(v) == 3}
    n = len(complete)
    print(f"Items rated by all three reviewers: {n}")

    # ------------------------------------------------------------------
    # 2. Compute human consensus and collect LLM verdicts
    # ------------------------------------------------------------------
    consensus    = []   # human 2-of-3 majority
    strict_llm   = []   # LLM strict verdict (pre-filled, same for all raters on a given item)
    lenient_llm  = []   # LLM lenient verdict

    disagreement_strict  = []
    disagreement_lenient = []

    for key, verdicts in complete.items():
        human_votes = [verdicts[r]["human_verdict"] for r in RATERS]
        yes_count = human_votes.count("YES")
        cons = "YES" if yes_count >= 2 else "NO"
        consensus.append(cons)

        # All raters see the same LLM verdicts — just take from first rater
        first = verdicts[RATERS[0]]
        s = first["verdict_strict"]
        l = first["verdict_lenient"]
        strict_llm.append(s)
        lenient_llm.append(l)

        if cons != s:
            disagreement_strict.append((key, cons, s,
                                        {r: verdicts[r]["human_verdict"] for r in RATERS}))
        if cons != l:
            disagreement_lenient.append((key, cons, l,
                                         {r: verdicts[r]["human_verdict"] for r in RATERS}))

    # ------------------------------------------------------------------
    # 3. Agreement statistics
    # ------------------------------------------------------------------
    pct_strict  = 100 * sum(h == j for h, j in zip(consensus, strict_llm))  / n
    pct_lenient = 100 * sum(h == j for h, j in zip(consensus, lenient_llm)) / n
    k_strict    = cohens_kappa(consensus, strict_llm)
    k_lenient   = cohens_kappa(consensus, lenient_llm)

    # ------------------------------------------------------------------
    # 4. Pairwise inter-rater kappa
    # ------------------------------------------------------------------
    pair_kappas = []
    for i, r1 in enumerate(RATERS):
        for r2 in RATERS[i + 1:]:
            a = [complete[k][r1]["human_verdict"] for k in complete]
            b = [complete[k][r2]["human_verdict"] for k in complete]
            agree_pct = 100 * sum(x == y for x, y in zip(a, b)) / n
            kv = cohens_kappa(a, b)
            pair_kappas.append((r1, r2, agree_pct, kv))

    # ------------------------------------------------------------------
    # 5. Write output
    # ------------------------------------------------------------------
    lines = [
        "Human validation of LLM-as-judge (three-reviewer spot-check)",
        "=" * 62,
        "",
        f"Items rated by all three reviewers: {n}",
        f"Reviewers: {', '.join(RATERS)}",
        "",
        "Human consensus (2-of-3 majority) vs strict LLM judge:",
        f"  Agreement:     {pct_strict:.1f}%",
        f"  Cohen's kappa: {k_strict:.3f}",
        "",
        "Human consensus (2-of-3 majority) vs lenient LLM judge:",
        f"  Agreement:     {pct_lenient:.1f}%",
        f"  Cohen's kappa: {k_lenient:.3f}",
        "",
        "Inter-rater agreement (pairwise Cohen's kappa among humans):",
    ]
    for r1, r2, pct, kv in pair_kappas:
        lines.append(f"  {r1} vs {r2}: {pct:.1f}% agreement, kappa={kv:.3f}")

    if disagreement_strict:
        lines += ["", f"Items where human consensus disagrees with strict judge ({len(disagreement_strict)}):"]
        for key, cons, llm, hvotes in disagreement_strict:
            lines.append(f"  {key}: human_consensus={cons}, llm_strict={llm}, "
                         f"individual_votes={hvotes}")

    if disagreement_lenient:
        lines += ["", f"Items where human consensus disagrees with lenient judge ({len(disagreement_lenient)}):"]
        for key, cons, llm, hvotes in disagreement_lenient:
            lines.append(f"  {key}: human_consensus={cons}, llm_lenient={llm}, "
                         f"individual_votes={hvotes}")

    lines += [
        "",
        "---",
        "Interpretation guide:",
        "  kappa < 0.20  = slight agreement",
        "  kappa 0.20-0.40 = fair",
        "  kappa 0.40-0.60 = moderate",
        "  kappa 0.60-0.80 = substantial",
        "  kappa 0.80-1.00 = near-perfect",
        "",
        "Note: the strict judge requires verbatim/close paraphrase; humans tend",
        "to judge more leniently, so lower strict kappa is expected and normal.",
        "The lenient kappa is the primary validation metric to cite in the paper.",
    ]

    output = "\n".join(lines)
    print(output)
    OUT_TXT.write_text(output + "\n", encoding="utf-8")
    print(f"\nSaved to {OUT_TXT}")


if __name__ == "__main__":
    main()
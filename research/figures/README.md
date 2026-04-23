# Figures — Reference for Ritwika (LaTeX)

**Produced by:** Medhini Oak (Evaluation Owner)  
**Last updated:** April 2026  
**All files are in:** `research/figures/`

---

## Figure 1 — Headline result (use in §5 Results)

### `fig1_decay_strict.png`

**LaTeX:** `\includegraphics[width=\columnwidth]{figures/fig1_decay_strict}`

**What it shows:** Fact-preservation rate by day-of-origin for the Day-7 weekly magazine, using the strict LLM judge. X-axis = day the fact was introduced (1 = Monday, 7 = Sunday). Y-axis = fraction of facts introduced on that day that appear in the final magazine. Three lines: neutral (orange), stylized (green), decoupled (blue).

**Suggested caption:**

> Figure 1: Fact-preservation rate by day-of-origin under the strict judge. The neutral pipeline (orange) maintains ~95% preservation regardless of when a fact was introduced. The stylized pipeline (green) drops to near zero for Days 1–4, recovering only for Day-7 facts that have not yet been recursively compressed. The decoupled pipeline (blue) holds a stable ~83% across all days, recovering most of the faithfulness lost to stylization.

**Key numbers to cite in text:**

- Neutral overall preservation: **96.3%** (strict), 97.2% (lenient)
- Stylized overall preservation: **24.2%** (strict), 26.3% (lenient)
- Decoupled overall preservation: **82.9%** (strict), 85.6% (lenient)
- Day-7 spike for stylized: ~93% — because Day-7 facts enter the magazine directly without prior recursion
- Inter-judge agreement: κ = **0.898** (near-perfect)

**What to say in §5:**

> "Figure 1 shows the fact-preservation rate by day-of-origin. Under the stylized pipeline, facts introduced on Days 1–4 are preserved at rates of 4–13%, compared to 96–100% under the neutral pipeline — a drop of over 80 percentage points. The recovery to 93% on Day 7 is mechanistically expected: Day-7 facts enter the final magazine without having been recursively compressed, and thus escape the compounding attrition. The decoupled pipeline recovers most of this faithfulness loss, maintaining 80–85% preservation across all days of origin."

---

### `fig1_decay_lenient.png`

**LaTeX:** `\includegraphics[width=\columnwidth]{figures/fig1_decay_lenient}` (appendix only)

**What it shows:** Same as fig1_decay_strict but using the lenient judge. Use as a robustness check in the appendix. The pattern is nearly identical (κ = 0.898 between judges), confirming the headline finding is not an artifact of judge strictness.

**Suggested caption:**

> Figure A1: Fact-preservation rate by day-of-origin under the lenient judge. The pattern mirrors Figure 1 (strict judge), confirming robustness across judge configurations (κ = 0.898).

---

## Figure 2 — Fact-type breakdown (use in §5 Results or §6 Discussion)

### `fig2_decay_by_type_strict.png`

**LaTeX:** `\includegraphics[width=\textwidth]{figures/fig2_decay_by_type_strict}`

Note: use `\textwidth` not `\columnwidth` — this is a 4-panel figure that needs full page width.

**What it shows:** The same decay curves as Figure 1, broken into four panels by fact type: named_entity, quantitative, relational, emotional. Strict judge only.

**Suggested caption:**

> Figure 2: Fact-preservation rate by day-of-origin and fact type (strict judge). The stylized pipeline loses facts consistently across all four types, with near-zero preservation for Days 1–5. Quantitative facts are notably harder for the decoupled pipeline (0.50–0.65 on Days 4–5), likely because numeric precision requires explicit carry-through. Emotional facts show the smallest gap between neutral and decoupled, suggesting affective content is faithfully preserved by factual-state propagation alone.

**Key findings to highlight per panel:**

**named_entity** — Stylized drops to ~0% on Days 2–4. Neutral near-perfect. Decoupled ~80–100%. Named entities (people, places, organisations) are not protected by stylistic pressure — they are dropped wholesale.

**quantitative** — Most interesting decoupled result: decoupled drops to ~0.50 on Day 4–5, notably below its performance on other fact types. Numbers (distances, times, quantities) require verbatim or precise carry-through; the neutral state summary may paraphrase them away even without stylization. Flag this as a finding: "decoupled does not fully protect quantitative facts."

**relational** — Stylized near zero for Days 1–5, then rises to ~87% on Day 7. Decoupled holds 75–90%. Relational facts (social connections, interpersonal events) are among the hardest hit by stylization.

**emotional** — Surprisingly, stylized still drops emotional facts heavily (7–23% Days 1–6) despite a tabloid voice that might be expected to amplify emotions. The paparazzo persona apparently replaces the user's actual emotional facts with generic dramatic framing rather than preserving them.

---

## Table 1 — Overall preservation rates

### `summary_table.csv`

| pipeline  | n   | preservation_strict | preservation_lenient |
| --------- | --- | ------------------- | -------------------- |
| neutral   | 327 | 0.963               | 0.972                |
| stylized  | 327 | 0.242               | 0.263                |
| decoupled | 327 | 0.829               | 0.856                |

**LaTeX:** Typeset this by hand as Table 1. Suggested column headers: Pipeline, N facts judged, Strict preservation rate, Lenient preservation rate.

**Suggested caption:**

> Table 1: Overall fact-preservation rates across all weeks and days-of-origin. N = 327 per pipeline (15 weeks × ~22 facts/week). Rates computed as fraction of YES verdicts excluding UNCLEAR.

---

## Table 2 — Automatic metrics (RQ3)

From `data/judgments/automatic_metrics.csv` — typeset by hand:

| Pipeline  | ROUGE-1 | ROUGE-2 | ROUGE-L | BERTScore-F | G-Eval Faithfulness |
| --------- | ------- | ------- | ------- | ----------- | ------------------- |
| neutral   | 0.323   | 0.151   | 0.225   | 0.777       | 4.73                |
| stylized  | 0.171   | 0.063   | 0.091   | 0.739       | 3.67                |
| decoupled | 0.353   | 0.139   | 0.171   | 0.780       | 4.20                |

**Suggested caption:**

> Table 2: Aggregate automatic metrics for each pipeline. BERTScore F1 varies by only 0.04 across pipelines despite a 72-point gap in LLM-judged fact preservation, illustrating that semantic similarity metrics are insensitive to the compounding fact decay revealed by our day-of-origin diagnostic. G-Eval faithfulness detects the direction of the effect but underestimates its severity (stylized scores 3.67/5 despite preserving only 24.2% of facts).

---

## Inter-judge agreement

From `interjudge_agreement.txt`:

> Cohen's kappa (strict vs lenient): **0.898**  
> N judgments: 981

**Cite in §4 Methodology:**

> "Inter-judge agreement was κ = 0.898 (Cohen's kappa, N = 981), indicating near-perfect agreement between the strict and lenient judge configurations."

---

## What is still pending (as of Day 7)

- [ ] Human spot-check: Medhini + Ritwika + one more reviewer each rate ~17 items via `streamlit run spot_check.py`. Results go to `data/judgments/human_spotcheck.csv`. Share human-LLM agreement % and κ in team chat when done.
- [x] Figure polish: publication-quality figures (300 DPI, colorblind-safe Okabe-Ito palette, ACM column widths) — complete.
- [x] Final frozen figures: committed to `research/figures/`.

---

## File layout summary

```
research/figures/
├── fig1_decay_strict.png          \includegraphics[width=\columnwidth]{figures/fig1_decay_strict}
├── fig1_decay_lenient.png         appendix: \includegraphics[width=\columnwidth]{figures/fig1_decay_lenient}
├── fig2_decay_by_type_strict.png  \includegraphics[width=\textwidth]{figures/fig2_decay_by_type_strict}
├── summary_table.csv              → Table 1 (typeset by hand)
└── interjudge_agreement.txt       → cite κ = 0.898 in §4
```

Automatic metrics table (Table 2) is in `research/data/judgments/automatic_metrics.csv`.

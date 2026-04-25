"""
judge.py -- LLM-as-judge evaluator for fact preservation.

Given a summary and a list of pre-registered facts, we ask the judge model:
"For each fact, is it preserved (explicitly or by clear paraphrase) in this summary?"
Return YES / NO / UNCLEAR per fact.

We run TWO judges (two different prompts) and report both separately. Inter-judge
agreement (Cohen's kappa) goes in the paper's methods appendix.

This file also exposes `evaluate_pipeline_results` which walks a results directory
and produces a single CSV with per-(week, pipeline, day, fact) preservation flags.
That CSV is the input to analyze.py which produces the decay curves.

Usage:
    python judge.py --results_dir data/results --weeks_dir data/weeks --out data/judgments
"""

import argparse
import csv
import json
import pathlib
from llm_client import chat


# Two judge prompts for the two-judge design.
JUDGE_PROMPT_STRICT = """\
You are a strict evaluator. You will be given (1) a list of facts about a person's week and (2) a summary text. For each fact, decide whether the fact is preserved in the summary.

A fact is PRESERVED only if the summary explicitly states the fact OR states a clear paraphrase that a reasonable reader would recognize as the same fact. Partial mentions, vague references, or similar-but-different facts count as NOT preserved.

Return ONLY a JSON array. For each fact, in the same order as given, return an object:
  {"id": "<fact id>", "verdict": "YES" | "NO" | "UNCLEAR", "evidence": "<a short quoted snippet from the summary if YES, else empty string>"}

Return the JSON array only, no preamble, no code fences.
"""

JUDGE_PROMPT_LENIENT = """\
You are a careful evaluator of summaries. You will be given (1) a list of facts about a person's week and (2) a summary text. For each fact, decide whether the summary conveys the core of the fact.

Judge YES if the summary contains the fact in any reasonable form -- explicit mention, paraphrase, or embedded detail that carries the same meaning. Judge NO if the fact is absent or the summary says something contradictory. Judge UNCLEAR only if you genuinely cannot tell.

Return ONLY a JSON array. For each fact, in the same order as given, return an object:
  {"id": "<fact id>", "verdict": "YES" | "NO" | "UNCLEAR", "evidence": "<a short quoted snippet from the summary if YES, else empty string>"}

Return the JSON array only, no preamble, no code fences.
"""


def _format_facts_for_judge(facts: list) -> str:
    lines = []
    for f in facts:
        lines.append(f"{f['id']} [day {f['day']}, type {f['type']}]: {f['text']}")
    return "\n".join(lines)


def _parse_judge_output(text: str) -> list:
    text = text.strip()
    if text.startswith("```"):
        # Strip code fence if present
        text = text.split("```", 2)[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip("` \n")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to salvage a truncated/malformed response
        # Find the first [ and last ] and attempt again
        if "[" in text and "]" in text:
            text = text[text.index("["): text.rindex("]") + 1]
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                pass
        return []


def judge_summary(summary: str, facts: list, judge_prompt: str, model: str, tag: str) -> list:
    """Ask the judge to evaluate a single (summary, facts) pair. Returns list of verdict dicts."""
    if not summary.strip():
        return [{"id": f["id"], "verdict": "NO", "evidence": ""} for f in facts]

    user_msg = (
        f"FACTS:\n{_format_facts_for_judge(facts)}\n\n"
        f"SUMMARY:\n{summary}"
    )
    reply = chat(
        system=judge_prompt,
        messages=[{"role": "user", "content": user_msg}],
        model=model,
        temperature=0.0,
        max_tokens=2000,
        tag=tag,
    )
    verdicts = _parse_judge_output(reply)

    # Normalize: ensure every fact id has an entry
    verdict_by_id = {v.get("id", ""): v for v in verdicts if isinstance(v, dict)}
    normalized = []
    for f in facts:
        v = verdict_by_id.get(f["id"], {"id": f["id"], "verdict": "UNCLEAR", "evidence": ""})
        normalized.append({
            "id": f["id"],
            "verdict": v.get("verdict", "UNCLEAR"),
            "evidence": v.get("evidence", ""),
        })
    return normalized


def evaluate_one_artifact(summary: str, facts: list, artifact_label: str, judge_model: str) -> list:
    """Run both judges on one summary. Returns a list of per-fact rows with both verdicts."""
    strict = judge_summary(summary, facts, JUDGE_PROMPT_STRICT, judge_model, tag=f"judge_strict_{artifact_label}")
    lenient = judge_summary(summary, facts, JUDGE_PROMPT_LENIENT, judge_model, tag=f"judge_lenient_{artifact_label}")
    strict_by_id = {v["id"]: v for v in strict}
    lenient_by_id = {v["id"]: v for v in lenient}

    rows = []
    for f in facts:
        s = strict_by_id.get(f["id"], {"verdict": "UNCLEAR", "evidence": ""})
        l = lenient_by_id.get(f["id"], {"verdict": "UNCLEAR", "evidence": ""})
        rows.append({
            "fact_id": f["id"],
            "fact_day": f["day"],
            "fact_type": f["type"],
            "fact_text": f["text"],
            "verdict_strict": s["verdict"],
            "evidence_strict": s["evidence"],
            "verdict_lenient": l["verdict"],
            "evidence_lenient": l["evidence"],
        })
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--results_dir", default="data/results")
    parser.add_argument("--weeks_dir", default="data/weeks")
    parser.add_argument("--out", default="data/judgments")
    parser.add_argument("--judge_model", default="groq-llama-70b",
                        help="Model to use as the judge. Recommend keeping fixed across all runs.")
    parser.add_argument("--artifact", choices=["weekly_magazine", "all_daily"],
                        default="weekly_magazine",
                        help="Which summary to judge. 'weekly_magazine' = Day 7 output only. "
                             "'all_daily' = judge every daily summary (7x more calls).")
    parser.add_argument("--pipelines", nargs="+",
                        default=["neutral", "stylized", "decoupled"])
    parser.add_argument("--gen_model", default=None,
                        help="Only judge this generation model directory. "
                             "If omitted, judges all model dirs (original behaviour).")
    args = parser.parse_args()

    results_root = pathlib.Path(__file__).parent / args.results_dir
    weeks_root = pathlib.Path(__file__).parent / args.weeks_dir
    out_root = pathlib.Path(__file__).parent / args.out
    out_root.mkdir(parents=True, exist_ok=True)

    # Output CSV with one row per (week, pipeline, day_evaluated, fact)
    csv_path = out_root / f"judgments_{args.artifact}_{args.judge_model}.csv"
    write_header = not csv_path.exists()
    csvf = open(csv_path, "a", newline="", encoding="utf-8")
    writer = csv.DictWriter(csvf, fieldnames=[
        "week_id", "pipeline", "gen_model", "day_evaluated",
        "fact_id", "fact_day", "fact_type", "fact_text",
        "verdict_strict", "evidence_strict",
        "verdict_lenient", "evidence_lenient",
    ])
    if write_header:
        writer.writeheader()

    for week_dir in sorted(results_root.glob("week_*")):
        week_id_str = week_dir.name.replace("week_", "")
        week_id = int(week_id_str)
        week_path = weeks_root / f"week_{week_id:02d}.json"
        if not week_path.exists():
            print(f"No week file for {week_dir.name}, skipping.")
            continue
        week = json.loads(week_path.read_text(encoding="utf-8"))
        facts = week["facts"]

        for model_dir in week_dir.iterdir():
            if not model_dir.is_dir():
                continue
            gen_model = model_dir.name      
            if args.gen_model and gen_model != args.gen_model: 
                continue
            for pipeline_name in args.pipelines:
                result_path = model_dir / f"{pipeline_name}.json"
                if not result_path.exists():
                    continue
                result = json.loads(result_path.read_text(encoding="utf-8"))

                if args.artifact == "weekly_magazine":
                    summary = result["weekly_magazine"]
                    label = f"w{week_id:02d}_{pipeline_name}_{gen_model}_magazine"
                    rows = evaluate_one_artifact(summary, facts, label, args.judge_model)
                    print(f"  Judged week {week_id:02d} / {pipeline_name} / {gen_model} (magazine)")
                    for r in rows:
                        writer.writerow({
                            "week_id": week_id,
                            "pipeline": pipeline_name,
                            "gen_model": gen_model,
                            "day_evaluated": 7,
                            **r,
                        })
                else:
                    # all_daily: judge every day's summary against all facts up to that day
                    for day in range(1, 8):
                        summary = result["daily_summaries"][str(day)]
                        # Only judge facts whose day <= current day
                        relevant_facts = [f for f in facts if f["day"] <= day]
                        label = f"w{week_id:02d}_{pipeline_name}_{gen_model}_day{day}"
                        rows = evaluate_one_artifact(summary, relevant_facts, label, args.judge_model)
                        print(f"  Judged week {week_id:02d} / {pipeline_name} / {gen_model} / day {day}")
                        for r in rows:
                            writer.writerow({
                                "week_id": week_id,
                                "pipeline": pipeline_name,
                                "gen_model": gen_model,
                                "day_evaluated": day,
                                **r,
                            })
                csvf.flush()

    csvf.close()
    print(f"\nJudgments written to {csv_path}")


if __name__ == "__main__":
    main()

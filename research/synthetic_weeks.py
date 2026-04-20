"""
synthetic_weeks.py -- Generate synthetic 7-day diary interview weeks.

Each synthetic week is specified by a persona and a list of pre-registered facts,
each tagged with a day-of-origin (1-7) and a fact type (named_entity, quantitative,
relational, emotional). We then use an LLM to turn each day's fact list into a
plausible Paparazzo-style interview transcript.

The pre-registered facts are the ground truth. They are what we later probe the
summaries against. Because we control the facts, we know exactly which facts
"should" appear in the Day-T summary, and we can measure their preservation as
a function of day-of-origin -- which is the core measurement of RQ1.

Usage:
    python synthetic_weeks.py              # generates all weeks to data/weeks/
    python synthetic_weeks.py --count 3    # generate only 3 weeks (for testing)
"""

import argparse
import json
import pathlib
import random
from llm_client import chat
from prompts import PAPARAZZO_INTERVIEWER_PROMPT

# ---------------------------------------------------------------------------
# Persona bank. Each persona is a short description that seeds the week.
# We deliberately pick varied ages, jobs, and life situations so reviewers
# don't see a monoculture of "tech startup founder in LA."
# ---------------------------------------------------------------------------
PERSONAS = [
    "A 28-year-old pastry chef in Berlin who just opened her own bakery and is training two new apprentices.",
    "A 45-year-old single father in Manchester, a secondary-school history teacher, whose teenage daughter is applying to universities this month.",
    "A 33-year-old indie musician on a 10-city European tour, currently in Prague, dealing with a sore throat and a broken guitar strap.",
    "A 52-year-old hospital nurse in Lisbon working night shifts, whose elderly mother moved in last week after a fall.",
    "A 24-year-old graduate student in Delhi finishing her thesis on marine biology, with fieldwork in Goa coming up in two weeks.",
    "A 39-year-old independent architect in Mexico City working on a controversial public library project with a tight deadline.",
    "A 61-year-old retired accountant in Dublin who recently took up competitive ballroom dancing with his wife.",
    "A 30-year-old social worker in Cape Town specializing in youth mentorship, balancing a heavy caseload and a new relationship.",
    "A 27-year-old software engineer in Tokyo, recently transferred from the Osaka office, living alone in a shared flat and learning to cook.",
    "A 47-year-old farmer in rural Romania running an organic vineyard, preparing for the autumn harvest with two seasonal workers.",
    "A 35-year-old physiotherapist in Oslo who also competes in amateur long-distance running, training for a marathon next month.",
    "A 42-year-old freelance journalist in Istanbul covering local politics, juggling three editors and an investigation that just got complicated.",
    "A 29-year-old ceramic artist in Porto opening her second studio, coordinating a group exhibition with four other artists.",
    "A 55-year-old secondary-school principal in Glasgow dealing with a difficult staff dispute and a school inspection next Friday.",
    "A 26-year-old veterinarian in Buenos Aires working at an animal shelter, dealing with an unexpected outbreak of kennel cough.",
]

# ---------------------------------------------------------------------------
# Fact-planning prompt -- asks the LLM to design the week's events as a
# structured fact list. We then use this list both as ground truth AND as
# the material to generate each day's interview from.
# ---------------------------------------------------------------------------
WEEK_PLANNER_PROMPT = """\
You are a writer planning a realistic 7-day diary for a specific person. I will give you a persona. Your job is to produce a plan for their week as a JSON object of facts, one fact per entry, spread across the 7 days.

REQUIREMENTS:
- Produce between 18 and 22 facts total.
- Each fact must be tagged with its DAY (1 to 7) and one of these TYPES:
    - "named_entity": a specific named person, place, organization, or branded object (e.g. "met with her accountant Pedro", "visited the Rialto Bridge")
    - "quantitative": a specific number, time, duration, or amount (e.g. "ran 12 kilometers", "spent 340 euros on the new oven")
    - "relational": an interaction or relationship update (e.g. "argued with her business partner", "reconnected with an old friend from university")
    - "emotional": a stated feeling or mood (e.g. "felt anxious about the bank meeting", "was proud of finishing the draft")
- Distribute facts roughly evenly across the 7 days (2-4 facts per day).
- Include a mix of all four types across the week. Aim for at least 3 of each type.
- Facts should fit the persona. Keep it realistic -- small, human, specific.
- Avoid fabricating dramatic events (no accidents, no deaths, no scandals). The point is an ordinary week.

Return ONLY a JSON object of this exact shape, nothing else, no preamble, no code fences:
{
  "persona": "<the persona you were given, verbatim>",
  "facts": [
    {"id": "f01", "day": 1, "type": "named_entity", "text": "..."},
    {"id": "f02", "day": 1, "type": "emotional", "text": "..."},
    ...
  ]
}

Every fact needs a unique id like "f01", "f02", ..., in order.
"""


DAILY_INTERVIEW_GENERATOR_PROMPT = """\
You will simulate a full daily diary interview between Snap (a Paparazzo-style reporter) and a user (the Star). You are given (1) the persona of the Star, (2) a list of facts that the Star mentioned on this specific day, and (3) the day number.

Produce a realistic back-and-forth transcript where Snap asks 6 to 8 probing questions and the Star's answers CONTAIN EVERY FACT in the given list. The Star should sound natural, not robotic -- embed the facts in real conversational responses. Snap should react, follow up, and push for detail.

Format the transcript like this:
Snap: <question>
Star: <answer>
Snap: <question>
Star: <answer>
...

The Star's answers must include all facts. The Star can add small natural color (tone, hesitation, minor asides) but MUST NOT add new concrete facts (no new names, places, numbers, feelings, decisions beyond what was in the list).

Return ONLY the transcript. No preamble, no closing commentary.
"""


def plan_week(persona: str, model: str = "groq-llama-70b") -> dict:
    """Generate the fact plan for one week. Returns the parsed JSON dict."""
    reply = chat(
        system=WEEK_PLANNER_PROMPT,
        messages=[{"role": "user", "content": f"Persona: {persona}"}],
        model=model,
        temperature=0.7,
        max_tokens=1500,
        tag="week_planner",
    )
    # Strip code fences if the model added them despite instructions.
    text = reply.strip()
    if text.startswith("```"):
        text = text.split("```", 2)[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip("` \n")
    return json.loads(text)


def generate_daily_interview(persona: str, day: int, day_facts: list, model: str = "groq-llama-70b") -> str:
    """Generate the Snap <-> Star transcript for one day, embedding the given facts."""
    facts_text = "\n".join(f"- {f['text']}  [type: {f['type']}]" for f in day_facts)
    user_msg = (
        f"Persona: {persona}\n\n"
        f"Day number: {day}\n\n"
        f"Facts the Star must mention today:\n{facts_text}"
    )
    return chat(
        system=DAILY_INTERVIEW_GENERATOR_PROMPT,
        messages=[{"role": "user", "content": user_msg}],
        model=model,
        temperature=0.7,
        max_tokens=1500,
        tag=f"daily_interview_day{day}",
    )


def build_week(persona: str, week_id: int, model: str = "groq-llama-70b") -> dict:
    """Build one complete synthetic week: fact plan + 7 daily transcripts."""
    print(f"  Planning week {week_id}...")
    plan = plan_week(persona, model=model)

    # Group facts by day
    facts_by_day = {d: [] for d in range(1, 8)}
    for f in plan["facts"]:
        if f["day"] in facts_by_day:
            facts_by_day[f["day"]].append(f)

    transcripts = {}
    for day in range(1, 8):
        day_facts = facts_by_day[day]
        if not day_facts:
            # Rare, but possible: skip empty days by adding one filler
            day_facts = [{"id": f"filler_d{day}", "day": day, "type": "emotional",
                         "text": "felt the day passed quietly without anything remarkable"}]
            plan["facts"].append(day_facts[0])
        print(f"    Generating interview for day {day}...")
        transcripts[day] = generate_daily_interview(persona, day, day_facts, model=model)

    return {
        "week_id": week_id,
        "persona": persona,
        "facts": plan["facts"],
        "facts_by_day": {str(d): facts_by_day[d] for d in range(1, 8)},
        "transcripts": {str(d): transcripts[d] for d in range(1, 8)},
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=15,
                        help="Number of synthetic weeks to generate (default 15).")
    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed for persona selection.")
    parser.add_argument("--model", default="groq-llama-70b",
                        help="Model to use for generation.")
    parser.add_argument("--out", default="data/weeks",
                        help="Output directory (relative to research/).")
    args = parser.parse_args()

    random.seed(args.seed)
    out_dir = pathlib.Path(__file__).parent / args.out
    out_dir.mkdir(parents=True, exist_ok=True)

    # Sample without replacement so no two weeks share a persona (if count <= len(PERSONAS))
    if args.count <= len(PERSONAS):
        chosen = random.sample(PERSONAS, args.count)
    else:
        chosen = random.choices(PERSONAS, k=args.count)

    for i, persona in enumerate(chosen, start=1):
        out_path = out_dir / f"week_{i:02d}.json"
        if out_path.exists():
            print(f"[{i}/{args.count}] week_{i:02d}.json already exists, skipping.")
            continue
        print(f"[{i}/{args.count}] Building week with persona: {persona[:60]}...")
        week = build_week(persona, week_id=i, model=args.model)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(week, f, indent=2, ensure_ascii=False)
        print(f"    Saved to {out_path}")

    print(f"\nDone. {args.count} weeks in {out_dir}")


if __name__ == "__main__":
    main()

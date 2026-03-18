"""
data_generation.py – Stub for generating synthetic training data using GPT-4.

Run this script (once the stubs are implemented) to produce question-answer
pairs that will be used to fine-tune the Paparazzo model.
"""

import os
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


def generate_interview_qa_pairs(
    n_samples: int = 100,
    job_role: str = "Software Engineer",
    output_path: Optional[str] = None,
) -> list[dict]:
    """Generate synthetic interview Q&A pairs using GPT-4.

    Args:
        n_samples:   Number of question-answer pairs to generate.
        job_role:    Target job role to tailor the questions to.
        output_path: If provided, save the generated data as a JSONL file at
                     this path.

    Returns:
        A list of dicts with keys 'question' and 'answer'.

    TODO:
        - Build a prompt that instructs GPT-4 to generate realistic interview
          questions and high-quality STAR-method answers for the given role.
        - Parse the model's JSON output into structured records.
        - Write records to ``output_path`` if specified.
        - Add deduplication and quality-filtering logic.
    """
    # Placeholder – replace with actual OpenAI API calls
    raise NotImplementedError("generate_interview_qa_pairs is not yet implemented.")


def save_to_jsonl(records: list[dict], path: str) -> None:
    """Persist a list of records to a JSONL file.

    Args:
        records: List of dicts to serialize.
        path:    Destination file path.

    TODO:
        - Implement JSONL serialization using the ``json`` standard library.
    """
    raise NotImplementedError("save_to_jsonl is not yet implemented.")


if __name__ == "__main__":
    output_file = os.path.join(os.path.dirname(__file__), "data", "synthetic_qa.jsonl")
    pairs = generate_interview_qa_pairs(n_samples=200, output_path=output_file)
    print(f"Generated {len(pairs)} Q&A pairs → {output_file}")

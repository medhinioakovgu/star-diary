"""
llm_client.py -- Thin wrapper around Groq and OpenAI APIs.

All API calls in the research pipeline go through this module. This gives us one place to:
  - set deterministic parameters (temperature=0 for evaluation, 0.7 for generation)
  - log every call to disk for reproducibility
  - swap models by changing one line

Usage:
    from llm_client import chat

    # For generation (interviewer, summarizer)
    reply = chat(
        system="You are ...",
        messages=[{"role": "user", "content": "Hello"}],
        model="groq-llama-70b",
        temperature=0.7,
    )

    # For evaluation (LLM-as-judge)
    reply = chat(
        system="You are a strict evaluator.",
        messages=[{"role": "user", "content": "..."}],
        model="groq-llama-70b",
        temperature=0.0,  # deterministic
    )
"""

import os
import json
import time
import pathlib
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# ---------------------------------------------------------------------------
# Model registry -- add more models here as needed.
# Each entry maps a short model name to (client_kwargs, model_id).
# ---------------------------------------------------------------------------
MODEL_REGISTRY = {
    "groq-llama-70b": {
        "base_url": "https://api.groq.com/openai/v1",
        "api_key_env": "GROQ_API_KEY",
        "model_id": "llama-3.3-70b-versatile",
    },
    "groq-llama-8b": {
        "base_url": "https://api.groq.com/openai/v1",
        "api_key_env": "GROQ_API_KEY",
        "model_id": "llama-3.1-8b-instant",
    },
    "openai-4o-mini": {
        "base_url": "https://api.openai.com/v1",
        "api_key_env": "OPENAI_API_KEY",
        "model_id": "gpt-4o-mini",
    },
    "openai-4.1-mini": {
        "base_url": "https://api.openai.com/v1",
        "api_key_env": "OPENAI_API_KEY",
        "model_id": "gpt-4.1-mini",
    },
}

# Cache clients so we don't reconnect on every call
_CLIENT_CACHE = {}


def _get_client(model_name: str) -> OpenAI:
    if model_name not in MODEL_REGISTRY:
        raise ValueError(
            f"Unknown model '{model_name}'. Available: {list(MODEL_REGISTRY.keys())}"
        )
    if model_name not in _CLIENT_CACHE:
        cfg = MODEL_REGISTRY[model_name]
        api_key = os.getenv(cfg["api_key_env"])
        if not api_key:
            raise RuntimeError(
                f"Environment variable {cfg['api_key_env']} not set. "
                f"Add it to your .env file."
            )
        _CLIENT_CACHE[model_name] = OpenAI(api_key=api_key, base_url=cfg["base_url"])
    return _CLIENT_CACHE[model_name]


# ---------------------------------------------------------------------------
# Call logging -- every LLM call is appended to logs/llm_calls.jsonl for audit.
# This is the record reviewers care about: which model, which prompt, what temp.
# ---------------------------------------------------------------------------
LOG_DIR = pathlib.Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "llm_calls.jsonl"


def _log_call(record: dict) -> None:
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


# ---------------------------------------------------------------------------
# Main entry point.
# ---------------------------------------------------------------------------
def chat(
    system: str,
    messages: list[dict],
    model: str = "groq-llama-70b",
    temperature: float = 0.7,
    max_tokens: int = 1024,
    retries: int = 3,
    tag: str = "",
) -> str:
    """Send a chat completion request. Returns the assistant's text reply.

    Args:
        system:      System prompt (personality / instructions).
        messages:    List of {"role": "user"|"assistant", "content": str}.
        model:       Short model name from MODEL_REGISTRY.
        temperature: 0.0 for evaluation, 0.7 for generation.
        max_tokens:  Output length cap.
        retries:     Retry on transient API errors.
        tag:         Free-form tag for logging (e.g. "summarizer_neutral_day3").

    Returns:
        The assistant's reply as a string.
    """
    cfg = MODEL_REGISTRY[model]
    client = _get_client(model)

    full_messages = [{"role": "system", "content": system}] + messages

    last_err = None
    for attempt in range(retries):
        try:
            t0 = time.time()
            response = client.chat.completions.create(
                model=cfg["model_id"],
                messages=full_messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            elapsed = time.time() - t0
            reply = response.choices[0].message.content or ""

            _log_call({
                "ts": datetime.utcnow().isoformat(),
                "tag": tag,
                "model": model,
                "model_id": cfg["model_id"],
                "temperature": temperature,
                "max_tokens": max_tokens,
                "system_prompt_chars": len(system),
                "user_messages_chars": sum(len(m["content"]) for m in messages),
                "reply_chars": len(reply),
                "elapsed_s": round(elapsed, 2),
                "usage": response.usage.model_dump() if response.usage else None,
            })
            return reply
        except Exception as e:
            last_err = e
            wait = 2 ** attempt
            print(f"[llm_client] API error (attempt {attempt+1}/{retries}): {e}. Retrying in {wait}s...")
            time.sleep(wait)

    raise RuntimeError(f"All {retries} attempts failed. Last error: {last_err}")


if __name__ == "__main__":
    # Smoke test -- run this file directly to check your API key works.
    print("Testing Groq connection...")
    reply = chat(
        system="You are a helpful assistant.",
        messages=[{"role": "user", "content": "Say 'hello research team' in exactly three words."}],
        model="groq-llama-70b",
        temperature=0.0,
        tag="smoke_test",
    )
    print(f"Reply: {reply}")
    print(f"Log written to: {LOG_FILE}")

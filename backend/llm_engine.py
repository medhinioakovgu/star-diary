"""
llm_engine.py – LLM abstraction layer for the Star-Interview Diary backend.

Currently powered by the OpenAI API (gpt-4o-mini).
TODO: Replace or augment with a local PyTorch / HuggingFace model once
      fine-tuning in research/train_lora.py is complete.
"""

import os

from dotenv import load_dotenv
from openai import OpenAI

from prompts import PAPARAZZO_SYSTEM_PROMPT

load_dotenv()

# ---------------------------------------------------------------------------
# OpenAI client
# ---------------------------------------------------------------------------
_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ---------------------------------------------------------------------------
# TODO (local model): Import your fine-tuned HuggingFace model here once ready.
# Example:
#   from transformers import AutoTokenizer, AutoModelForCausalLM
#   import torch
#
#   _tokenizer = AutoTokenizer.from_pretrained("./models/paparazzo-lora")
#   _local_model = AutoModelForCausalLM.from_pretrained(
#       "./models/paparazzo-lora",
#       torch_dtype=torch.float16,
#       device_map="auto",
#   )
# ---------------------------------------------------------------------------


def generate_paparazzo_reply(chat_history: list, user_message: str) -> str:
    """Generate a reply from Paparazzo given the conversation history and the
    latest user message.

    Args:
        chat_history: A list of dicts with 'role' and 'content' keys,
                      representing the conversation so far (excluding the
                      current user message).
        user_message: The latest message from the user.

    Returns:
        The assistant's reply as a plain string.
    """
    messages = [{"role": "system", "content": PAPARAZZO_SYSTEM_PROMPT}]
    messages.extend(chat_history)
    messages.append({"role": "user", "content": user_message})

    # ---------------------------------------------------------------------------
    # OpenAI API call
    # Replace this block with local model inference when switching to HuggingFace.
    # ---------------------------------------------------------------------------
    response = _client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.7,
        max_tokens=512,
    )
    return response.choices[0].message.content or ""

    # ---------------------------------------------------------------------------
    # TODO (local model): Swap the block above with something like:
    #
    #   inputs = _tokenizer(messages_to_prompt(messages), return_tensors="pt").to(_local_model.device)
    #   output_ids = _local_model.generate(**inputs, max_new_tokens=512)
    #   return _tokenizer.decode(output_ids[0], skip_special_tokens=True)
    # ---------------------------------------------------------------------------

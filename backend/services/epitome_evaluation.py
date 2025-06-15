import json

import replicate
import os

# Use secret manager
from backend.utils.check_secrets import get_secret

# Load API token
REPLICATE_API_TOKEN = get_secret("REPLICATE_API_TOKEN")
replicate.Client(api_token=REPLICATE_API_TOKEN)

# def call_epitome_model(user_input, llm_response):
#     # TEMPORARY MOCK
#     return {
#         "emotional_reactions": {"score": 2, "rationale": "You seem very caring."},
#         "interpretations": {"score": 2, "rationale": "You understood their pain."},
#         "explorations": {"score": 2, "rationale": "You invited further sharing."}
#     }


def call_epitome_model(user_input: str, llm_response: str) -> dict:
    prompt = f"""
SYSTEM: You are an EPITOME evaluator. You must output *only* valid JSON—no extra text, no markdown, no apologies, no keys beyond the three shown.

Schema (exactly this order):
{{
  "emotional_reactions": {{ "score": <0–2>, "rationale": "<string>" }},
  "interpretations":    {{ "score": <0–2>, "rationale": "<string>" }},
  "explorations":       {{ "score": <0–2>, "rationale": "<string>" }}
}}

USER:
Seeker: {user_input}

Responder: {llm_response}

Now evaluate and emit *only* the JSON object conforming to the schema above. Stop generation immediately after the closing `}}`.
"""

    # 1) stream=False so we get a single return value
    raw = replicate.run(
        "meta/meta-llama-3-8b-instruct",
        input={"prompt": prompt},
        stream=False,
        temperature=0.0,
        stop=["}}"],
    )

    # 2) If it ever comes back as a list of strings, coalesce it
    if isinstance(raw, list):
        raw = "".join(raw)

    # 3) Trim whitespace/newlines
    raw = raw.strip()

    # 4) Parse JSON (or raise a clear error)
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Invalid JSON from model: {raw!r}") from e
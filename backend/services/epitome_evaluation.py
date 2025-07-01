import json
import re
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

def safe_parse_json(raw: str) -> dict:
    # strip any ```json fences
    cleaned = re.sub(r"^```json\s*|\s*```$", "", raw.strip(), flags=re.IGNORECASE)
    # pull out the first “{……”
    if "{" in cleaned:
        cleaned = cleaned[cleaned.index("{"):]
    # pull up to the last “}”
    if "}" in cleaned:
        cleaned = cleaned[: cleaned.rfind("}") + 1]
    # auto-balance braces
    open_braces  = cleaned.count("{")
    close_braces = cleaned.count("}")
    if open_braces > close_braces:
        cleaned += "}" * (open_braces - close_braces)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Still invalid JSON after cleaning: {cleaned!r}") from e



def call_epitome_model(user_input: str, llm_response: str) -> dict:
    prompt = f"""
SYSTEM: You are an EPITOME evaluator. You must output *only* valid JSON—no extra text, no markdown, no apologies, no keys beyond the three shown.

IMPORTANT: For each category, your “rationale” field must be the exact substring (verbatim) from the Responder’s text that most directly justifies the score. Do NOT paraphrase or explain—just quote the snippet.

Schema (exactly this order):
{{
  "emotional_reactions": {{ "score": <0–2>, "rationale": "<verbatim text excerpt>" }},
  "interpretations":    {{ "score": <0–2>, "rationale": "<verbatim text excerpt>" }},
  "explorations":       {{ "score": <0–2>, "rationale": "<verbatim text excerpt>" }}
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
    )

    # 2) If it ever comes back as a list of strings, coalesce it
    if isinstance(raw, list):
        raw = "".join(raw)

    # 3) Trim whitespace/newlines
    raw = raw.strip()

    # Use our safe parser instead of direct json.loads
    return safe_parse_json(raw)
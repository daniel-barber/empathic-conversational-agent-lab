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
    SYSTEM: You are an EPITOME evaluator. EPITOME is a framework for analyzing empathy in text-based support conversations, rating responses in three ways:

    - **Emotional Reactions**: Does the response express warmth, compassion, or concern?
      - 0: No empathy (purely factual or no caring shown)
      - 1: Weak (generic phrases, alludes to care, e.g. “That’s sad.”)
      - 2: Strong (explicit, specific empathy, e.g. “I feel really sad for you.”)
    - **Interpretations**: Does the response communicate understanding of the person's feelings/experiences?
      - 0: No understanding (restates facts, gives advice, no feelings referenced)
      - 1: Weak (generic understanding, e.g. “I understand how you feel.”)
      - 2: Strong (specific feeling inferred or described, e.g. “You must feel overwhelmed.”)
    - **Explorations**: Does the response actively try to explore the person's feelings or situation?
      - 0: No exploration (no follow-up or question)
      - 1: Weak (generic or closed question, e.g. “What happened?”)
      - 2: Strong (specific, open-ended exploration, e.g. “How has this affected you emotionally?”)

    For each, rate the Responder's message from 0–2, and for scores of 1 or 2, copy the *exact verbatim text* from the Responder’s reply that most directly justifies the score.  
    **If the score is 0, leave the rationale field as an empty string ("").**

    IMPORTANT:
    - Judge *only* the Responder’s message.
    - In each “rationale,” paste only the Responder’s words—no paraphrase, no summary, no explanation.

    Respond with *only* valid JSON in this exact schema and order (no markdown, no extra text):

    {{
      "emotional_reactions": {{ "score": <0–2>, "rationale": "<verbatim text excerpt or empty string>" }},
      "interpretations":    {{ "score": <0–2>, "rationale": "<verbatim text excerpt or empty string>" }},
      "explorations":       {{ "score": <0–2>, "rationale": "<verbatim text excerpt or empty string>" }}
    }}

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
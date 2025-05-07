import replicate
import os

# Use secret manager
from backend.utils.check_secrets import get_secret

# Load API token
REPLICATE_API_TOKEN = get_secret("REPLICATE_API_TOKEN")
replicate.Client(api_token=REPLICATE_API_TOKEN)

def call_epitome_model(user_input, llm_response):
    # TEMPORARY MOCK
    return {
        "emotional_reactions": {"score": 2, "rationale": "You seem very caring."},
        "interpretations": {"score": 2, "rationale": "You understood their pain."},
        "explorations": {"score": 2, "rationale": "You invited further sharing."}
    }


# def call_epitome_model(user_input, llm_response):
#     prompt = f"""
# Seeker: {user_input}
#
# Responder: {llm_response}
#
# Evaluate the responder using EPITOME:
# - Emotional Reactions
# - Interpretations
# - Explorations
#
# Give scores (0=none, 1=weak, 2=strong) and short rationales.
# Return JSON format like:
# {{
#   "emotional_reactions": {{ "score": 2, "rationale": "..." }},
#   "interpretations": {{ "score": 2, "rationale": "..." }},
#   "explorations": {{ "score": 2, "rationale": "..." }}
# }}
# """
#
#     output = replicate.run(
#         "meta/meta-llama-3-8b",
#         input={"prompt": prompt}
#     )
#
#     return output

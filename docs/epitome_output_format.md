# EPITOME Evaluation Output Format

## 1. Overview

The output JSON structure represents the evaluation of an LLM agent's response to a seeker's message according to the EPITOME framework for empathy assessment.

Each evaluation contains three components:
- Emotional Reactions
- Interpretations
- Explorations

For each component:
- A numerical **score** between 0 and 2 is provided.
- A **rationale** (text excerpt or paraphrase) from the agent's response justifying the score is included.

---

## 2. Top-Level Structure

The JSON output consists of three top-level fields:

- `emotional_reactions`
- `interpretations`
- `explorations`

Each top-level field contains:
- `score`: integer (0, 1, or 2)
- `rationale`: string (direct quote or paraphrase from agent response)

---

## 3. Field-Level Documentation

| Field | Type | Description |
|------|------|-------------|
| `emotional_reactions.score` | integer (0–2) | Level of emotional warmth, compassion, or resonance expressed by the agent. |
| `emotional_reactions.rationale` | string | A portion of the agent's text that supports the emotional reaction score. If no evidence, set empty string `""`. |
| `interpretations.score` | integer (0–2) | Degree to which the agent demonstrates cognitive understanding of the seeker's emotions or experiences. |
| `interpretations.rationale` | string | A portion of the agent's text that supports the interpretation score. If no evidence, set empty string `""`. |
| `explorations.score` | integer (0–2) | Extent to which the agent invites the seeker to explore or share more about their feelings or experiences. |
| `explorations.rationale` | string | A portion of the agent's text that supports the exploration score. If no evidence, set empty string `""`. |

**Notes:**
- `score = 0` indicates no communication of the mechanism.
- `score = 1` indicates weak or implicit communication.
- `score = 2` indicates strong, explicit communication.

---

## 4. Example JSON Output

```json
{
  "emotional_reactions": {
    "score": 2,
    "rationale": "I'm really sorry you're feeling that way."
  },
  "interpretations": {
    "score": 2,
    "rationale": "It sounds like you're carrying a lot of pain and it's weighing you down."
  },
  "explorations": {
    "score": 2,
    "rationale": "Would you like to talk about what feels the heaviest for you right now?"
  }
}

"""
modules/gemini_client.py
Gemini API wrapper — initialisation, calling, and JSON parsing.
"""

import json
import re
import google.generativeai as genai

_model = None


def init_gemini(api_key: str):
    """Configure Gemini with the provided API key."""
    global _model
    genai.configure(api_key=api_key)
    _model = genai.GenerativeModel("gemini-2.5-flash")


def _call(prompt: str) -> str:
    """Raw call to Gemini. Returns response text."""
    if _model is None:
        raise RuntimeError("Gemini not initialised. Call init_gemini(api_key) first.")
    response = _model.generate_content(prompt)
    return response.text.strip()


def _call_json(prompt: str) -> dict:
    """Call Gemini and parse the response as JSON. Returns {} on failure."""
    raw = _call(prompt)
    # Strip ```json ... ``` fences
    clean = re.sub(r"```(?:json)?", "", raw).replace("```", "").strip()
    try:
        return json.loads(clean)
    except json.JSONDecodeError:
        # Try to extract the first { ... } block
        match = re.search(r"\{.*\}", clean, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
    return {}


# ── Public API ────────────────────────────────────────────────────────────────

def generate_topics(topic_prompt: str) -> list[str]:
    """Return up to 5 topic category strings."""
    raw = _call(topic_prompt)
    topics = [t.strip() for t in raw.split(",") if t.strip()]
    return topics[:5]


def generate_first_question(question_prompt: str, system_prompt: str) -> str:
    """Generate the opening question for a topic."""
    full_prompt = f"{system_prompt}\n\n{question_prompt}"
    return _call(full_prompt)


def evaluate_answer(eval_prompt: str, system_prompt: str) -> dict:
    """
    Evaluate a candidate's answer.
    Returns a dict with keys: score, feedback, dimension_scores,
    star_check, local_confidence, next_question, is_last.
    """
    full_prompt = f"{system_prompt}\n\n{eval_prompt}"
    result = _call_json(full_prompt)

    # Defensive defaults so the app never crashes on bad JSON
    result.setdefault("score", 5)
    result.setdefault("feedback", "No feedback generated.")
    result.setdefault("dimension_scores", {
        "Technical Depth": 5, "Communication": 5, "Problem Solving": 5,
        "Behavioural": 5, "Confidence": 5,
    })
    result.setdefault("star_check", {"applicable": False, "used_star": None, "missing": []})
    result.setdefault("local_confidence", 50)
    result.setdefault("next_question", "")
    result.setdefault("is_last", False)

    return result


def generate_hint(hint_prompt: str, system_prompt: str = "") -> str:
    """Return a hint nudge for the current question."""
    full = f"{system_prompt}\n\n{hint_prompt}" if system_prompt else hint_prompt
    return _call(full)


def generate_report(report_prompt: str) -> dict:
    """
    Generate a final performance report.
    Returns a dict with keys: summary, strengths, weak_areas, top_tip.
    """
    result = _call_json(report_prompt)
    result.setdefault("summary", "Session complete.")
    result.setdefault("strengths", [])
    result.setdefault("weak_areas", [])
    result.setdefault("top_tip", "Keep practising!")
    return result
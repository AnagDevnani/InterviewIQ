"""
modules/session.py
Session state initialisation and all stateful helpers.
"""

import time
import streamlit as st

# Dimensions used for radar chart
DIMENSIONS = ["Technical Depth", "Communication", "Problem Solving", "Behavioural", "Confidence"]

_DEFAULTS = {
    # Navigation
    "step": "input",                 # input → configure → topics → interview → report

    # Job details
    "company": "",
    "role": "",
    "jd": "",
    "resume_text": "",

    # Session config
    "persona": "Friendly HR",
    "difficulty": "Auto",
    "num_questions": 8,

    # Interview runtime
    "current_topic": "",
    "system_prompt": "",
    "current_question": "",
    "question_number": 0,
    "chat_history": [],              # [{"role": "assistant"|"user", "content": "..."}]

    # Per-answer tracking
    "scores": [],
    "feedbacks": [],
    "dimension_scores_all": [],      # list of dicts per question
    "confidence_scores": [],
    "star_results": [],
    "answer_times": [],

    # Counters
    "hints_used": 0,
    "skips_used": 0,
    "hint_used_this_turn": False,

    # Timer
    "_answer_start": None,

    # Report
    "report": None,

    # Topics
    "topics": [],
}


def init_session():
    """Initialise all session state keys that are not yet set."""
    for key, default in _DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = default


def reset_full():
    """Reset everything back to defaults."""
    for key, default in _DEFAULTS.items():
        st.session_state[key] = default


def reset_interview():
    """
    Keep job details + configuration but reset the interview runtime state.
    Used when retrying with a different topic.
    """
    interview_keys = [
        "current_topic", "system_prompt", "current_question", "question_number",
        "chat_history", "scores", "feedbacks", "dimension_scores_all",
        "confidence_scores", "star_results", "answer_times",
        "hints_used", "skips_used", "hint_used_this_turn", "_answer_start", "report",
    ]
    for key in interview_keys:
        st.session_state[key] = _DEFAULTS[key]


# ── Chat helpers ──────────────────────────────────────────────────────────────

def push_chat(role: str, content: str):
    """Append a message to the chat history."""
    st.session_state.chat_history.append({"role": role, "content": content})


def chat_history_as_text() -> str:
    """Flatten chat history to a readable string for prompt injection."""
    lines = []
    for msg in st.session_state.chat_history:
        label = "Interviewer" if msg["role"] == "assistant" else "Candidate"
        # Strip HTML tags for cleaner prompt context
        import re
        clean = re.sub(r"<[^>]+>", "", msg["content"])
        lines.append(f"{label}: {clean}")
    return "\n".join(lines)


# ── Timer helpers ─────────────────────────────────────────────────────────────

def start_answer_timer():
    st.session_state._answer_start = time.time()


def stop_answer_timer() -> int:
    """Return elapsed seconds since the timer was started."""
    if st.session_state._answer_start is None:
        return 0
    elapsed = int(time.time() - st.session_state._answer_start)
    st.session_state._answer_start = None
    return elapsed


# ── Score helpers ─────────────────────────────────────────────────────────────

def get_overall_score() -> float:
    """Return mean score across all answered questions."""
    scores = st.session_state.scores
    return round(sum(scores) / len(scores), 2) if scores else 0.0


def get_avg_dimension_scores() -> dict:
    """Return averaged dimension scores across all answered questions."""
    all_dims = st.session_state.dimension_scores_all
    if not all_dims:
        return {}
    avg = {}
    for dim in DIMENSIONS:
        values = [d.get(dim, 5) for d in all_dims]
        avg[dim] = round(sum(values) / len(values), 1)
    return avg
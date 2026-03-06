"""
prompts/templates.py
All prompt templates used throughout the interview bot.
"""

# ── Persona descriptions injected into every session prompt ──────────────────

PERSONA_DESCRIPTIONS = {
    "Friendly HR": (
        "You are a warm, encouraging HR interviewer. "
        "Your tone is conversational and supportive. "
        "You celebrate good answers and gently guide on weak ones."
    ),
    "Tough Technical Panel": (
        "You are a senior engineer on a rigorous technical panel. "
        "Your tone is direct and no-nonsense. "
        "You probe deeply, ask follow-ups, and challenge vague answers."
    ),
    "Stress Interview": (
        "You are conducting a deliberate stress interview. "
        "You are skeptical, occasionally devil's advocate, and push back on every answer. "
        "Your goal is to test composure under pressure."
    ),
}

# ── Difficulty descriptions ───────────────────────────────────────────────────

DIFFICULTY_DESCRIPTIONS = {
    "Easy": "Ask beginner-level questions suitable for freshers or entry-level candidates.",
    "Medium": "Ask mid-level questions that require 1–3 years of experience.",
    "Hard": "Ask senior-level, deep-dive questions that require 4+ years of expertise.",
    "Auto": (
        "Infer the candidate's seniority from their resume and calibrate difficulty automatically. "
        "Adapt as the interview progresses based on the quality of their answers."
    ),
}


def build_session_system_prompt(
    company: str,
    role: str,
    persona: str,
    difficulty: str,
    resume_text: str,
    jd_text: str,
    num_questions: int,
) -> str:
    """
    Master system prompt built once per session.
    Injected at the top of every Gemini call.
    """
    persona_desc = PERSONA_DESCRIPTIONS.get(persona, PERSONA_DESCRIPTIONS["Friendly HR"])
    diff_desc = DIFFICULTY_DESCRIPTIONS.get(difficulty, DIFFICULTY_DESCRIPTIONS["Auto"])

    return f"""
You are an interviewer at {company}.
{persona_desc}

ROLE BEING INTERVIEWED FOR: {role if role else "inferred from resume/JD"}
DIFFICULTY LEVEL: {difficulty} — {diff_desc}
TOTAL QUESTIONS THIS SESSION: {num_questions}

CANDIDATE RESUME:
{resume_text if resume_text else "Not provided."}

JOB DESCRIPTION:
{jd_text if jd_text else "Not provided."}

RULES:
- Ask ONE question at a time. Never ask multiple questions in a single turn.
- Stay in character as described above at all times.
- Do not reveal scores or internal evaluations during the interview.
- Base questions on the resume and JD context above.
""".strip()


def topic_generation_prompt(company: str, jd_text: str, resume_text: str) -> str:
    return f"""
Analyze the following job description and candidate resume for a role at {company}.
Identify exactly 5 distinct interview topic categories most relevant to this specific role and candidate.

Examples of categories: Technical Skills, System Design, Behavioral, Problem Solving, 
Domain Knowledge, Leadership, Communication, Data Structures & Algorithms, etc.

JOB DESCRIPTION:
{jd_text}

CANDIDATE RESUME:
{resume_text if resume_text else "Not provided."}

Return ONLY the 5 topic names separated by commas. No numbering, no explanation.
""".strip()


def first_question_prompt(system_prompt: str, topic: str) -> str:
    return f"""
{system_prompt}

--- BEGIN INTERVIEW ---
Topic for this session: {topic}

Ask your first interview question on this topic. 
Ask ONLY the question — no preamble, no explanation.
""".strip()


def eval_and_next_question_prompt(
    system_prompt: str,
    history: list,
    user_answer: str,
    topic: str,
    question_number: int,
    total_questions: int,
    used_hint: bool,
) -> str:
    """
    Evaluate the candidate's answer and (if not last question) generate the next question.
    Returns structured JSON.
    """
    history_text = "\n".join(
        [
            f"{'Interviewer' if m['role'] == 'assistant' else 'Candidate'}: {m['content']}"
            for m in history
        ]
    )
    hint_note = " (Note: The candidate used a hint for this answer — factor a small penalty into the score.)" if used_hint else ""

    is_last = question_number >= total_questions

    next_q_instruction = (
        "Set next_question to an empty string and is_last to true."
        if is_last
        else f"Generate the next relevant interview question on the topic '{topic}'. Make sure it's different from all previous questions."
    )

    return f"""
{system_prompt}

--- CONVERSATION SO FAR ---
{history_text}
Candidate: {user_answer}{hint_note}

--- YOUR TASK ---
Evaluate the candidate's latest answer. Return ONLY a valid JSON object with this exact structure:

{{
  "feedback": "2-3 sentence evaluation of the answer quality",
  "score": <integer 1-10>,
  "star_check": {{
    "applicable": <true if this was a behavioral question, false otherwise>,
    "used_star": <true/false>,
    "missing_components": ["Situation", "Task", "Action", "Result"]  // list only the missing ones
  }},
  "local_confidence": <integer 0-100, your estimate of how confident the candidate seemed>,
  "next_question": "<the next interview question or empty string if last>",
  "is_last": <true/false>
}}

{next_q_instruction}

Return ONLY the JSON. No markdown, no explanation outside the JSON.
""".strip()


def hint_prompt(system_prompt: str, question: str) -> str:
    return f"""
{system_prompt}

The candidate is struggling with this interview question and has asked for a hint:
"{question}"

Give a subtle nudge — point them in the right direction WITHOUT giving away the answer.
Keep it to 1-2 sentences maximum.
""".strip()


def report_synthesis_prompt(
    company: str,
    role: str,
    topic: str,
    session_data: list,
    skipped_count: int,
    hint_count: int,
) -> str:
    """
    session_data = list of dicts with keys: question, answer, score, feedback, local_confidence
    """
    qa_summary = "\n\n".join(
        [
            f"Q{i+1}: {item['question']}\n"
            f"Answer: {item.get('answer', '[Skipped]')}\n"
            f"Score: {item.get('score', 0)}/10\n"
            f"Feedback: {item.get('feedback', '')}"
            for i, item in enumerate(session_data)
        ]
    )

    return f"""
You are analyzing a completed mock interview session.

Company: {company}
Role: {role}
Topic: {topic}
Questions Skipped: {skipped_count}
Hints Used: {hint_count}

--- FULL SESSION ---
{qa_summary}

Based on this session, provide:
1. Top 2 genuine strengths shown by the candidate (specific, not generic)
2. Top 2 areas needing improvement (specific, actionable)
3. One overall recommendation for this candidate

Return ONLY a valid JSON object:
{{
  "strengths": ["strength 1", "strength 2"],
  "weaknesses": ["weakness 1", "weakness 2"],
  "overall_recommendation": "..."
}}
""".strip()
"""
config.py
All app-wide constants, prompt builders, and configuration.
"""

# ── App identity ──────────────────────────────────────────────────────────────
APP_TITLE = "InterviewIQ"
APP_ICON  = "🎯"

# ── Penalties ─────────────────────────────────────────────────────────────────
HINT_PENALTY = 1   # deducted from score when hint is used
SKIP_PENALTY = 0   # skips don't affect score, just tracked

# ── Difficulty ────────────────────────────────────────────────────────────────
DIFFICULTY_OPTIONS = ["Auto", "Easy", "Medium", "Hard"]

DIFFICULTY_DESCRIPTIONS = {
    "Auto":   "AI calibrates difficulty from your resume seniority and adapts as you answer.",
    "Easy":   "Entry-level questions suitable for freshers or career switchers.",
    "Medium": "Mid-level questions requiring 1–3 years of hands-on experience.",
    "Hard":   "Senior-level deep-dives requiring 4+ years of expertise.",
}

# ── Personas ──────────────────────────────────────────────────────────────────
PERSONA_OPTIONS = ["Friendly HR", "Tough Technical Panel", "Stress Interview"]

PERSONA_DESCRIPTIONS = {
    "Friendly HR": (
        "You are a warm, supportive HR interviewer. Your tone is conversational and encouraging. "
        "You acknowledge good answers positively and guide gently on weaker ones."
    ),
    "Tough Technical Panel": (
        "You are a senior engineer on a rigorous technical panel. You are direct and no-nonsense. "
        "You probe answers deeply, ask follow-up questions, and challenge vague or incomplete responses."
    ),
    "Stress Interview": (
        "You are running a deliberate stress interview. You are skeptical, push back on every answer, "
        "play devil's advocate, and test the candidate's composure under sustained pressure."
    ),
}

# ── Prompt builders ───────────────────────────────────────────────────────────

def build_system_prompt(company, role, persona, difficulty, resume_text, jd, num_questions):
    persona_desc = PERSONA_DESCRIPTIONS.get(persona, PERSONA_DESCRIPTIONS["Friendly HR"])
    diff_desc    = DIFFICULTY_DESCRIPTIONS.get(difficulty, DIFFICULTY_DESCRIPTIONS["Auto"])
    return f"""
You are an interviewer at {company or "a top company"}.
{persona_desc}

ROLE: {role or "inferred from resume/JD"}
DIFFICULTY: {difficulty} — {diff_desc}
TOTAL QUESTIONS THIS SESSION: {num_questions}

CANDIDATE RESUME:
{resume_text or "Not provided."}

JOB DESCRIPTION:
{jd or "Not provided."}

RULES:
- Ask exactly ONE question per turn. Never combine multiple questions.
- Stay strictly in character at all times.
- Do not reveal internal scoring or evaluation logic during the interview.
- Ground your questions in the resume and JD context above.
""".strip()


def build_topic_prompt(company, jd, resume_text):
    return f"""
Analyse the job description and candidate resume for a role at {company or "this company"}.
Identify exactly 5 distinct interview topic categories most relevant to this specific role and candidate profile.

JOB DESCRIPTION:
{jd or "Not provided."}

CANDIDATE RESUME:
{resume_text or "Not provided."}

Return ONLY the 5 topic names separated by commas. No numbering, no explanation, no extra text.
""".strip()


def build_first_question_prompt(topic, company, role):
    return f"""
Topic for this interview session: {topic}
Company: {company or "the company"}
Role: {role or "the target role"}

Ask your first interview question on this topic.
Output ONLY the question — no preamble, no label, no explanation.
""".strip()


def build_eval_prompt(company, role, topic, question, answer,
                      question_number, total_questions, chat_history_text,
                      used_hint=False):
    hint_note = " (The candidate used a hint — apply a small score penalty.)" if used_hint else ""
    is_last   = question_number >= total_questions

    next_instruction = (
        'Set "next_question" to "" and "is_last" to true.'
        if is_last else
        f'Generate the next distinct interview question on "{topic}". '
        f'It must not repeat any question already asked in the conversation.'
    )

    return f"""
You are evaluating a mock interview answer.

Company: {company} | Role: {role} | Topic: {topic}
Question #{question_number} of {total_questions}

--- CONVERSATION SO FAR ---
{chat_history_text}

--- LATEST ANSWER ---
Candidate: {answer}{hint_note}

Evaluate the answer and return ONLY a valid JSON object with this exact schema:

{{
  "score": <integer 1-10>,
  "feedback": "<2-3 sentence evaluation>",
  "dimension_scores": {{
    "Technical Depth": <1-10>,
    "Communication": <1-10>,
    "Problem Solving": <1-10>,
    "Behavioural": <1-10>,
    "Confidence": <1-10>
  }},
  "star_check": {{
    "applicable": <true if behavioural question, else false>,
    "used_star": <true/false or null if not applicable>,
    "missing": ["Situation","Task","Action","Result"]
  }},
  "local_confidence": <0-100>,
  "next_question": "<next question string or empty string>",
  "is_last": <true/false>
}}

{next_instruction}
Return ONLY the JSON. No markdown fences, no explanation outside the JSON.
""".strip()


def build_hint_prompt(question, system_prompt):
    return f"""
{system_prompt}

The candidate is struggling with this question and has asked for a hint:
"{question}"

Give a subtle nudge that points them in the right direction WITHOUT revealing the answer.
Keep it to 1-2 sentences only.
""".strip()


def build_report_prompt(company, role, persona, all_feedbacks, overall_score, skips, hints):
    feedbacks_text = "\n".join(
        [f"Q{i+1}: {fb}" for i, fb in enumerate(all_feedbacks)]
    )
    return f"""
Synthesise a post-interview report for a candidate who just completed a mock interview.

Company: {company} | Role: {role} | Persona: {persona}
Overall Score: {overall_score:.1f}/10
Hints used: {hints} | Questions skipped: {skips}

Per-question feedback received:
{feedbacks_text}

Return ONLY a valid JSON object:
{{
  "summary": "<2-3 sentence overall summary>",
  "strengths": ["<specific strength 1>", "<specific strength 2>"],
  "weak_areas": ["<specific weakness 1>", "<specific weakness 2>"],
  "top_tip": "<one concrete, actionable improvement tip>"
}}

Be specific — avoid generic statements. Base everything on the feedback above.
Return ONLY the JSON. No markdown, no explanation.
""".strip()
"""
app.py — InterviewIQ | Production-grade Streamlit Application
"""

import os
import streamlit as st
import time

# ── .env loading (local dev) ──────────────────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from config import (
    APP_TITLE, APP_ICON,
    DIFFICULTY_OPTIONS, DIFFICULTY_DESCRIPTIONS,
    PERSONA_OPTIONS, PERSONA_DESCRIPTIONS,
    build_system_prompt, build_topic_prompt,
    build_first_question_prompt, build_eval_prompt,
    build_hint_prompt, build_report_prompt,
    HINT_PENALTY, SKIP_PENALTY,
)
from modules.session import (
    init_session, reset_interview, reset_full,
    start_answer_timer, stop_answer_timer,
    push_chat, chat_history_as_text,
    get_overall_score, get_avg_dimension_scores,
)
from modules.parser import parse_uploaded_file
from modules.gemini_client import (
    init_gemini,
    generate_topics, generate_first_question,
    evaluate_answer, generate_hint, generate_report,
)
from modules.charts import (
    score_timeline_chart, radar_chart,
    answer_time_chart, star_donut_chart, per_question_bar,
)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="InterviewIQ",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ══════════════════════════════════════════════════════════════════════════════
# DESIGN SYSTEM
# Aesthetic: Editorial/Terminal hybrid. Monochrome base with electric teal.
# Fonts: "Instrument Serif" for headings (editorial weight), "JetBrains Mono"
#        for body (developer-grade legibility). Feels like a Bloomberg terminal
#        crossed with a design agency portfolio.
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=JetBrains+Mono:wght@300;400;500;600&display=swap');

/* ── Reset & Base ─────────────────────────────────── */
*, *::before, *::after { box-sizing: border-box; }

html, body, [class*="css"], .stApp {
    background-color: #080A0F !important;
    color: #C8CDD8 !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 14px;
}

/* ── Hide Streamlit chrome ────────────────────────── */
#MainMenu, footer, header,
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="collapsedControl"] { display: none !important; }

/* ── Layout ───────────────────────────────────────── */
.block-container {
    max-width: 1100px !important;
    padding: 3rem 2rem 4rem !important;
}
section[data-testid="stSidebar"] { display: none !important; }

/* ── Typography ───────────────────────────────────── */
h1, h2 {
    font-family: 'Instrument Serif', serif !important;
    color: #F0F2F7 !important;
    font-weight: 400 !important;
    letter-spacing: -0.02em;
}
h3, h4 {
    font-family: 'JetBrains Mono', monospace !important;
    color: #E0E4EF !important;
    font-weight: 500 !important;
    font-size: 0.85rem !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
}

/* ── Horizontal rule ──────────────────────────────── */
hr { border: none; border-top: 1px solid #161B28 !important; margin: 2rem 0; }

/* ── Cards ────────────────────────────────────────── */
.iq-card {
    background: #0D1119;
    border: 1px solid #1A2035;
    border-radius: 4px;
    padding: 1.5rem;
    margin-bottom: 1rem;
    transition: border-color 0.2s ease;
}
.iq-card:hover { border-color: #2A3555; }
.iq-card-accent { border-left: 2px solid #00E5B4 !important; }
.iq-card-warn   { border-left: 2px solid #F5A623 !important; }
.iq-card-danger { border-left: 2px solid #FF5252 !important; }

/* ── Chat bubbles ─────────────────────────────────── */
.bubble-wrap { display: flex; flex-direction: column; gap: 1rem; margin-bottom: 1.5rem; }

.bubble-bot {
    display: flex;
    gap: 0.75rem;
    align-items: flex-start;
    max-width: 82%;
}
.bubble-bot-avatar {
    width: 30px; height: 30px;
    background: #00E5B4;
    border-radius: 2px;
    display: flex; align-items: center; justify-content: center;
    font-size: 14px;
    flex-shrink: 0;
    margin-top: 2px;
}
.bubble-bot-body {
    background: #0D1119;
    border: 1px solid #1A2035;
    border-radius: 0 6px 6px 6px;
    padding: 1rem 1.25rem;
    line-height: 1.7;
    font-size: 0.9rem;
    color: #D4D9E8;
}

.bubble-user {
    display: flex;
    gap: 0.75rem;
    align-items: flex-start;
    max-width: 82%;
    margin-left: auto;
    flex-direction: row-reverse;
}
.bubble-user-avatar {
    width: 30px; height: 30px;
    background: #1E2840;
    border: 1px solid #2A3555;
    border-radius: 2px;
    display: flex; align-items: center; justify-content: center;
    font-size: 14px;
    flex-shrink: 0;
    margin-top: 2px;
}
.bubble-user-body {
    background: #111827;
    border: 1px solid #1E2840;
    border-radius: 6px 0 6px 6px;
    padding: 1rem 1.25rem;
    line-height: 1.7;
    font-size: 0.9rem;
    color: #C8CDD8;
    text-align: right;
}

.feedback-card {
    background: #080D15;
    border: 1px solid #00E5B430;
    border-radius: 4px;
    padding: 1.1rem 1.4rem;
    margin-top: 0.5rem;
    line-height: 1.8;
    font-size: 0.875rem;
    color: #A8B4CC;
}

/* ── Pills & badges ───────────────────────────────── */
.pill {
    display: inline-flex; align-items: center;
    padding: 0.25rem 0.75rem;
    border-radius: 2px;
    font-size: 0.75rem;
    font-weight: 500;
    letter-spacing: 0.05em;
    margin: 0.15rem;
    border: 1px solid;
}
.pill-green  { color: #00E5B4; border-color: #00E5B440; background: #00E5B40D; }
.pill-amber  { color: #F5A623; border-color: #F5A62340; background: #F5A6230D; }
.pill-red    { color: #FF5252; border-color: #FF525240; background: #FF52520D; }
.pill-blue   { color: #6B9FFF; border-color: #6B9FFF40; background: #6B9FFF0D; }

/* ── Score badge ──────────────────────────────────── */
.score-hero {
    font-family: 'Instrument Serif', serif;
    font-size: 5rem;
    color: #00E5B4;
    line-height: 1;
    font-weight: 400;
}
.score-label {
    font-size: 0.7rem;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: #4A5568;
    margin-top: 0.3rem;
}

/* ── Progress bar ─────────────────────────────────── */
.stProgress > div > div > div > div {
    background: linear-gradient(90deg, #00E5B4, #00B4E5) !important;
    border-radius: 0 !important;
}
.stProgress > div > div {
    background: #1A2035 !important;
    border-radius: 0 !important;
    height: 3px !important;
}

/* ── Streamlit native inputs ──────────────────────── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div {
    background: #0D1119 !important;
    border: 1px solid #1A2035 !important;
    border-radius: 4px !important;
    color: #C8CDD8 !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 13px !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: #00E5B4 !important;
    box-shadow: 0 0 0 1px #00E5B420 !important;
}
[data-baseweb="select"] > div {
    background: #0D1119 !important;
    border-color: #1A2035 !important;
}
.stFileUploader > div {
    background: #0D1119 !important;
    border: 1px dashed #1A2035 !important;
    border-radius: 4px !important;
}
.stFileUploader > div:hover { border-color: #00E5B4 !important; }
.stSlider > div > div > div > div { background: #00E5B4 !important; }

/* ── Buttons ──────────────────────────────────────── */
.stButton > button {
    background: transparent !important;
    border: 1px solid #1A2035 !important;
    color: #8892A4 !important;
    border-radius: 4px !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 12px !important;
    letter-spacing: 0.04em !important;
    padding: 0.5rem 1rem !important;
    transition: all 0.15s ease !important;
    font-weight: 400 !important;
}
.stButton > button:hover {
    border-color: #00E5B4 !important;
    color: #00E5B4 !important;
    background: #00E5B408 !important;
}

/* Primary CTA button */
.btn-primary > button {
    background: #00E5B4 !important;
    border: 1px solid #00E5B4 !important;
    color: #080A0F !important;
    font-weight: 600 !important;
    letter-spacing: 0.06em !important;
}
.btn-primary > button:hover {
    background: #00CCА0 !important;
    color: #080A0F !important;
    border-color: #00CCА0 !important;
}

/* Danger button */
.btn-danger > button {
    border-color: #FF525230 !important;
    color: #FF5252 !important;
}
.btn-danger > button:hover {
    border-color: #FF5252 !important;
    background: #FF52520D !important;
    color: #FF5252 !important;
}

/* ── Radio buttons ────────────────────────────────── */
.stRadio > div { gap: 0.5rem !important; }
.stRadio > div > label {
    background: #0D1119;
    border: 1px solid #1A2035;
    border-radius: 4px;
    padding: 0.6rem 1rem !important;
    transition: all 0.15s ease;
    cursor: pointer;
    font-size: 13px !important;
}
.stRadio > div > label:hover { border-color: #2A3555; }

/* ── Expander ─────────────────────────────────────── */
[data-testid="stExpander"] {
    background: #0D1119 !important;
    border: 1px solid #1A2035 !important;
    border-radius: 4px !important;
}
[data-testid="stExpander"]:hover { border-color: #2A3555 !important; }

/* ── Metric ───────────────────────────────────────── */
[data-testid="stMetricValue"] {
    font-family: 'Instrument Serif', serif !important;
    color: #F0F2F7 !important;
    font-size: 2rem !important;
}
[data-testid="stMetricLabel"] { color: #4A5568 !important; font-size: 0.7rem !important; }

/* ── Topic card ───────────────────────────────────── */
.topic-card {
    background: #0D1119;
    border: 1px solid #1A2035;
    border-radius: 4px;
    padding: 1.4rem 1rem;
    text-align: center;
    transition: all 0.2s ease;
    cursor: pointer;
}
.topic-card:hover {
    border-color: #00E5B4;
    background: #00E5B408;
}
.topic-number {
    font-size: 0.65rem;
    letter-spacing: 0.15em;
    color: #00E5B4;
    text-transform: uppercase;
    margin-bottom: 0.4rem;
}
.topic-name {
    font-size: 0.9rem;
    font-weight: 500;
    color: #D4D9E8;
}

/* ── Watermark / logo ─────────────────────────────── */
.iq-logo {
    font-family: 'Instrument Serif', serif;
    font-size: 1.1rem;
    color: #2A3555;
    letter-spacing: 0.02em;
}
.iq-logo span { color: #00E5B4; }

/* ── Step indicator ───────────────────────────────── */
.step-bar {
    display: flex;
    gap: 6px;
    margin-bottom: 2.5rem;
}
.step-dot {
    height: 3px;
    flex: 1;
    border-radius: 0;
    background: #1A2035;
    transition: background 0.3s ease;
}
.step-dot.active { background: #00E5B4; }
.step-dot.done   { background: #004D3F; }

/* ── Scrollbar ────────────────────────────────────── */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: #080A0F; }
::-webkit-scrollbar-thumb { background: #1A2035; border-radius: 2px; }
::-webkit-scrollbar-thumb:hover { background: #2A3555; }

/* ── Chat input ───────────────────────────────────── */
[data-testid="stChatInput"] {
    border-top: 1px solid #1A2035 !important;
    background: #080A0F !important;
}
[data-testid="stChatInput"] > div {
    background: #0D1119 !important;
    border: 1px solid #1A2035 !important;
    border-radius: 4px !important;
}
[data-testid="stChatInputSubmitButton"] > button {
    background: #00E5B4 !important;
    border: none !important;
    color: #080A0F !important;
}

/* ── Spinner ──────────────────────────────────────── */
.stSpinner > div { border-top-color: #00E5B4 !important; }

/* ── Success / Error / Info ───────────────────────── */
.stSuccess, .stInfo, .stWarning, .stError {
    border-radius: 4px !important;
    font-size: 0.85rem !important;
}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# INIT
# ══════════════════════════════════════════════════════════════════════════════
init_session()

# ── API key: .env → st.secrets → stop ────────────────────────────────────────
api_key = os.environ.get("GEMINI_API_KEY", "")
if not api_key:
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
    except Exception:
        pass

if not api_key:
    st.markdown("""
    <div style="max-width:500px; margin:8rem auto; text-align:center;">
        <div style="font-family:'Instrument Serif',serif; font-size:2rem; color:#F0F2F7; margin-bottom:1rem;">
            Missing API Key
        </div>
        <div style="color:#4A5568; font-size:0.85rem; line-height:1.8;">
            Create a <code style="color:#00E5B4">.env</code> file in the project root with:<br><br>
            <code style="background:#0D1119; border:1px solid #1A2035; padding:0.5rem 1rem; display:inline-block; border-radius:4px; color:#00E5B4;">
                GEMINI_API_KEY=your_key_here
            </code><br><br>
            Then restart the app with <code style="color:#00E5B4">streamlit run app.py</code>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

init_gemini(api_key)


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def step_bar(current: int, total: int = 5):
    """Render a minimal top step progress indicator."""
    dots = ""
    for i in range(1, total + 1):
        cls = "active" if i == current else ("done" if i < current else "")
        dots += f'<div class="step-dot {cls}"></div>'
    st.markdown(f'<div class="step-bar">{dots}</div>', unsafe_allow_html=True)


def logo():
    st.markdown('<div class="iq-logo">Interview<span>IQ</span></div>', unsafe_allow_html=True)


STEP_MAP = {"input": 1, "configure": 2, "topics": 3, "interview": 4, "report": 5}


# ══════════════════════════════════════════════════════════════════════════════
# STEP 1 — INPUT
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.step == "input":

    logo()
    step_bar(1)

    st.markdown("""
    <h1 style="font-size:3.2rem; margin-bottom:0.25rem;">
        Your next role<br><em>starts here.</em>
    </h1>
    <p style="color:#4A5568; margin-bottom:2.5rem; font-size:0.85rem; letter-spacing:0.02em;">
        AI mock interviews tailored to your resume and target role.
    </p>
    """, unsafe_allow_html=True)

    col_l, spacer, col_r = st.columns([5, 1, 5])

    with col_l:
        st.markdown('<h3 style="margin-bottom:1rem;">01 / Resume</h3>', unsafe_allow_html=True)
        resume_file = st.file_uploader(
            "Upload resume", type=["pdf", "docx"],
            label_visibility="collapsed",
            help="PDF or DOCX — text extracted locally, never stored.",
        )
        if resume_file:
            resume_text, err = parse_uploaded_file(resume_file)
            if err:
                st.error(err)
            else:
                st.session_state.resume_text = resume_text
                st.markdown(
                    f'<div class="pill pill-green">✓ {len(resume_text):,} chars extracted</div>',
                    unsafe_allow_html=True,
                )
                with st.expander("Preview text"):
                    st.code(resume_text[:600] + ("…" if len(resume_text) > 600 else ""),
                            language=None)

    with col_r:
        st.markdown('<h3 style="margin-bottom:1rem;">02 / Role</h3>', unsafe_allow_html=True)
        st.session_state.company = st.text_input(
            "Company", value=st.session_state.company,
            placeholder="e.g. Google, Stripe, Anthropic…",
            label_visibility="collapsed",
        )
        st.caption("Company")
        st.session_state.role = st.text_input(
            "Role", value=st.session_state.role,
            placeholder="e.g. Senior Backend Engineer, PM…",
            label_visibility="collapsed",
        )
        st.caption("Target Role")
        st.session_state.jd = st.text_area(
            "Job Description", value=st.session_state.jd,
            placeholder="Paste the full job description here…",
            height=180, label_visibility="collapsed",
        )
        st.caption("Job Description")

    st.markdown("<br>", unsafe_allow_html=True)

    can_proceed = bool(
        st.session_state.company.strip() and
        st.session_state.role.strip() and
        st.session_state.jd.strip()
    )

    c1, c2, c3 = st.columns([2, 3, 2])
    with c2:
        st.markdown('<div class="btn-primary">', unsafe_allow_html=True)
        if st.button(
            "Continue to Configuration →",
            disabled=not can_proceed,
            use_container_width=True,
        ):
            st.session_state.step = "configure"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
        if not can_proceed:
            st.markdown(
                '<p style="text-align:center;color:#4A5568;font-size:0.75rem;margin-top:0.5rem;">'
                'Company, Role and Job Description are required.</p>',
                unsafe_allow_html=True,
            )


# ══════════════════════════════════════════════════════════════════════════════
# STEP 2 — CONFIGURE
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.step == "configure":

    logo()
    step_bar(2)
    st.markdown('<h1>Configure<br><em>your session.</em></h1>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    col_a, spacer, col_b = st.columns([5, 1, 5])

    with col_a:
        st.markdown('<h3 style="margin-bottom:1rem;">Difficulty</h3>', unsafe_allow_html=True)
        chosen_diff = st.radio(
            "Difficulty", DIFFICULTY_OPTIONS,
            index=DIFFICULTY_OPTIONS.index(st.session_state.difficulty),
            label_visibility="collapsed",
        )
        st.session_state.difficulty = chosen_diff
        st.markdown(
            f'<div class="iq-card iq-card-accent" style="margin-top:0.75rem">'
            f'<span style="color:#4A5568;font-size:0.8rem;">{DIFFICULTY_DESCRIPTIONS[chosen_diff]}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

        st.markdown('<h3 style="margin:1.5rem 0 0.75rem;">Questions</h3>', unsafe_allow_html=True)
        st.session_state.num_questions = st.slider(
            "Questions", min_value=5, max_value=15,
            value=st.session_state.num_questions,
            label_visibility="collapsed",
        )
        st.markdown(
            f'<span class="pill pill-blue">{st.session_state.num_questions} questions per session</span>',
            unsafe_allow_html=True,
        )

    with col_b:
        st.markdown('<h3 style="margin-bottom:1rem;">Interviewer Persona</h3>', unsafe_allow_html=True)
        chosen_persona = st.radio(
            "Persona", PERSONA_OPTIONS,
            index=PERSONA_OPTIONS.index(st.session_state.persona),
            label_visibility="collapsed",
        )
        st.session_state.persona = chosen_persona
        st.markdown(
            f'<div class="iq-card iq-card-accent" style="margin-top:0.75rem">'
            f'<span style="color:#4A5568;font-size:0.8rem;">{PERSONA_DESCRIPTIONS[chosen_persona]}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)
    nav_l, nav_m, nav_r = st.columns([2, 3, 2])
    with nav_l:
        if st.button("← Back", use_container_width=True):
            st.session_state.step = "input"
            st.rerun()
    with nav_r:
        st.markdown('<div class="btn-primary">', unsafe_allow_html=True)
        if st.button("Generate Topics →", use_container_width=True):
            with st.spinner("Analysing JD & resume…"):
                topics = generate_topics(
                    build_topic_prompt(
                        st.session_state.company,
                        st.session_state.jd,
                        st.session_state.resume_text,
                    )
                )
                st.session_state.topics = topics
                # ✅ FIX: pass all 7 required args to build_system_prompt
                st.session_state.system_prompt = build_system_prompt(
                    company=st.session_state.company,
                    role=st.session_state.role,
                    persona=st.session_state.persona,
                    difficulty=st.session_state.difficulty,
                    resume_text=st.session_state.resume_text,
                    jd=st.session_state.jd,
                    num_questions=st.session_state.num_questions,
                )
                st.session_state.step = "topics"
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# STEP 3 — TOPIC SELECTION
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.step == "topics":

    logo()
    step_bar(3)
    st.markdown('<h1>Pick your<br><em>battleground.</em></h1>', unsafe_allow_html=True)
    st.markdown(
        f'<p style="color:#4A5568;font-size:0.8rem;margin-bottom:2rem;">'
        f'{st.session_state.role} · {st.session_state.company} · '
        f'{st.session_state.difficulty} · {st.session_state.persona}</p>',
        unsafe_allow_html=True,
    )

    cols = st.columns(len(st.session_state.topics), gap="small")
    for i, topic in enumerate(st.session_state.topics):
        with cols[i]:
            st.markdown(
                f'<div class="topic-card">'
                f'<div class="topic-number">0{i+1}</div>'
                f'<div class="topic-name">{topic}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
            if st.button("Start →", key=f"topic_{i}", use_container_width=True):
                reset_interview()
                st.session_state.current_topic = topic
                # Re-attach system_prompt (reset_interview clears it)
                st.session_state.system_prompt = build_system_prompt(
                    company=st.session_state.company,
                    role=st.session_state.role,
                    persona=st.session_state.persona,
                    difficulty=st.session_state.difficulty,
                    resume_text=st.session_state.resume_text,
                    jd=st.session_state.jd,
                    num_questions=st.session_state.num_questions,
                )
                st.session_state.step = "interview"
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("← Back to Config"):
        st.session_state.step = "configure"
        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# STEP 4 — LIVE INTERVIEW
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.step == "interview":

    # ── Top bar ───────────────────────────────────────────────────────────────
    hdr_l, hdr_m, hdr_r = st.columns([4, 3, 2])
    with hdr_l:
        logo()
        st.markdown(
            f'<span style="color:#4A5568;font-size:0.75rem;">'
            f'{st.session_state.current_topic} · {st.session_state.persona} · {st.session_state.difficulty}'
            f'</span>',
            unsafe_allow_html=True,
        )
    with hdr_m:
        progress = (st.session_state.question_number / st.session_state.num_questions
                    if st.session_state.num_questions else 0)
        st.markdown(
            f'<div style="font-size:0.7rem;color:#4A5568;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:4px;">'
            f'Question {st.session_state.question_number} of {st.session_state.num_questions}</div>',
            unsafe_allow_html=True,
        )
        st.progress(min(progress, 1.0))
    with hdr_r:
        avg_so_far = (sum(st.session_state.scores) / len(st.session_state.scores)
                      if st.session_state.scores else 0)
        st.markdown(
            f'<div style="text-align:right;">'
            f'<span style="font-family:Instrument Serif,serif;font-size:1.6rem;color:#00E5B4;">{avg_so_far:.1f}</span>'
            f'<span style="color:#4A5568;font-size:0.7rem;"> / 10 avg</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown('<hr style="margin:1rem 0 1.5rem;">', unsafe_allow_html=True)

    # ── Generate first question if needed ─────────────────────────────────────
    if len(st.session_state.chat_history) == 0:
        with st.spinner("Preparing your first question…"):
            first_q = generate_first_question(
                build_first_question_prompt(
                    st.session_state.current_topic,
                    st.session_state.company,
                    st.session_state.role,
                ),
                st.session_state.system_prompt,
            )
            push_chat("assistant", first_q)
            st.session_state.current_question = first_q
            st.session_state.question_number = 1
            start_answer_timer()
            st.rerun()

    # ── Render chat ───────────────────────────────────────────────────────────
    st.markdown('<div class="bubble-wrap">', unsafe_allow_html=True)
    for msg in st.session_state.chat_history:
        if msg["role"] == "assistant":
            st.markdown(
                f'<div class="bubble-bot">'
                f'<div class="bubble-bot-avatar">AI</div>'
                f'<div class="bubble-bot-body">{msg["content"]}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div class="bubble-user">'
                f'<div class="bubble-user-avatar">You</div>'
                f'<div class="bubble-user-body">{msg["content"]}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
    st.markdown("</div>", unsafe_allow_html=True)

    # ── Hint / Skip ───────────────────────────────────────────────────────────
    hint_col, skip_col, spacer = st.columns([1.4, 1.4, 6])
    with hint_col:
        st.markdown('<div class="btn-danger">', unsafe_allow_html=True)
        hint_clicked = st.button("💡 Hint", key="hint_btn", use_container_width=True,
                                 help=f"Get a nudge — costs {HINT_PENALTY} pt")
        st.markdown("</div>", unsafe_allow_html=True)
    with skip_col:
        st.markdown('<div class="btn-danger">', unsafe_allow_html=True)
        skip_clicked = st.button("⏭ Skip", key="skip_btn", use_container_width=True,
                                 help="Skip this question")
        st.markdown("</div>", unsafe_allow_html=True)

    if hint_clicked:
        with st.spinner("Generating hint…"):
            hint_text = generate_hint(
                build_hint_prompt(st.session_state.current_question, st.session_state.current_topic),
                st.session_state.system_prompt,
            )
        st.session_state.hints_used += 1
        st.markdown(
            f'<div class="iq-card iq-card-warn">'
            f'<span style="color:#F5A623;font-size:0.7rem;letter-spacing:0.1em;">HINT</span><br><br>'
            f'{hint_text}</div>',
            unsafe_allow_html=True,
        )

    if skip_clicked:
        elapsed = stop_answer_timer()
        st.session_state.skips_used += 1
        st.session_state.scores.append(0)
        st.session_state.dimension_scores_all.append(
            {d: 0 for d in ["Technical Depth", "Communication",
                             "Problem Solving", "Behavioural", "Confidence"]}
        )
        st.session_state.confidence_scores.append(0)
        st.session_state.feedbacks.append("Question skipped.")
        st.session_state.star_results.append({"used_star": None, "missing": []})
        st.session_state.answer_times.append(elapsed)
        push_chat("user", "<em style='color:#4A5568'>— skipped —</em>")

        if st.session_state.question_number >= st.session_state.num_questions:
            st.session_state.step = "report"
        else:
            st.session_state.question_number += 1
            with st.spinner("Next question…"):
                next_q = generate_first_question(
                    build_first_question_prompt(
                        st.session_state.current_topic,
                        st.session_state.company,
                        st.session_state.role,
                    ),
                    st.session_state.system_prompt,
                )
            push_chat("assistant", next_q)
            st.session_state.current_question = next_q
            start_answer_timer()
        st.rerun()

    # ── Answer input ──────────────────────────────────────────────────────────
    user_answer = st.chat_input("Type your answer…")

    if user_answer:
        elapsed = stop_answer_timer()
        push_chat("user", user_answer)
        st.session_state.answer_times.append(elapsed)

        with st.spinner("Evaluating…"):
            result = evaluate_answer(
                build_eval_prompt(
                    company=st.session_state.company,
                    role=st.session_state.role,
                    topic=st.session_state.current_topic,
                    question=st.session_state.current_question,
                    answer=user_answer,
                    question_number=st.session_state.question_number,
                    total_questions=st.session_state.num_questions,
                    chat_history_text=chat_history_as_text(),
                ),
                st.session_state.system_prompt,
            )

        score      = max(0, min(10, int(result.get("score", 5))))
        local_conf = max(0, min(100, int(result.get("local_confidence", 50))))
        feedback   = result.get("feedback", "")
        star_info  = result.get("star_check", {})

        st.session_state.scores.append(score)
        st.session_state.dimension_scores_all.append(
            result.get("dimension_scores",
                       {d: 5 for d in ["Technical Depth", "Communication",
                                       "Problem Solving", "Behavioural", "Confidence"]})
        )
        st.session_state.confidence_scores.append(local_conf)
        st.session_state.feedbacks.append(feedback)
        st.session_state.star_results.append(star_info)

        # Build feedback HTML
        score_cls = "pill-green" if score >= 7 else ("pill-amber" if score >= 5 else "pill-red")
        conf_cls  = "pill-green" if local_conf >= 65 else ("pill-amber" if local_conf >= 40 else "pill-red")

        star_badge = ""
        if star_info.get("used_star") is True:
            star_badge = '<span class="pill pill-green">✓ STAR</span>'
        elif star_info.get("used_star") is False:
            missing = ", ".join(star_info.get("missing", []))
            star_badge = f'<span class="pill pill-amber">⚠ STAR missing: {missing}</span>'

        timer_badge = f'<span class="pill pill-blue">⏱ {elapsed}s</span>'

        feedback_html = (
            f'<div class="feedback-card">'
            f'<div style="margin-bottom:0.75rem;">'
            f'<span class="pill {score_cls}">Score {score}/10</span>'
            f'<span class="pill {conf_cls}">Confidence {local_conf}%</span>'
            f'{star_badge}{timer_badge}'
            f'</div>'
            f'<div style="color:#8892A4;font-size:0.85rem;line-height:1.8;">{feedback}</div>'
            f'</div>'
        )

        next_q = result.get("next_question")
        is_last = (
            st.session_state.question_number >= st.session_state.num_questions
            or result.get("is_last", False)
            or not next_q
        )

        if is_last:
            push_chat("assistant",
                      feedback_html +
                      '<br><div style="color:#00E5B4;font-size:0.85rem;">✓ Interview complete — generating your report.</div>')
            st.session_state.step = "report"
        else:
            st.session_state.question_number += 1
            push_chat("assistant",
                      feedback_html +
                      f'<br><div style="margin-top:1rem;color:#D4D9E8;font-weight:500;">{next_q}</div>')
            st.session_state.current_question = next_q
            start_answer_timer()

        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# STEP 5 — REPORT
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.step == "report":

    overall  = get_overall_score()
    avg_dims = get_avg_dimension_scores()

    if st.session_state.report is None:
        with st.spinner("Synthesising your report…"):
            st.session_state.report = generate_report(
                build_report_prompt(
                    company=st.session_state.company,
                    role=st.session_state.role,
                    persona=st.session_state.persona,
                    all_feedbacks=st.session_state.feedbacks,
                    overall_score=overall,
                    skips=st.session_state.skips_used,
                    hints=st.session_state.hints_used,
                )
            )

    report  = st.session_state.report
    logo()
    step_bar(5)

    # ── Hero ──────────────────────────────────────────────────────────────────
    st.markdown(
        f'<h1 style="margin-bottom:0.25rem;">Session<br><em>complete.</em></h1>'
        f'<p style="color:#4A5568;font-size:0.8rem;margin-bottom:2.5rem;">'
        f'{st.session_state.role} · {st.session_state.company} · {st.session_state.current_topic}</p>',
        unsafe_allow_html=True,
    )

    grade = ("Excellent" if overall >= 8 else
             "Good" if overall >= 6 else
             "Needs Work" if overall >= 4 else "Keep Practising")
    grade_col = ("#00E5B4" if overall >= 8 else
                 "#6B9FFF" if overall >= 6 else
                 "#F5A623" if overall >= 4 else "#FF5252")

    avg_time = (sum(st.session_state.answer_times) / len(st.session_state.answer_times)
                if st.session_state.answer_times else 0)

    hero_l, hero_m, hero_r = st.columns([2, 4, 3])
    with hero_l:
        st.markdown(
            f'<div class="iq-card" style="text-align:center;padding:2rem 1rem;">'
            f'<div class="score-hero">{overall:.1f}</div>'
            f'<div class="score-label">overall score</div>'
            f'<div style="margin-top:0.8rem;font-size:0.8rem;color:{grade_col};">{grade}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with hero_m:
        st.markdown(
            f'<div class="iq-card" style="height:100%;">'
            f'<div style="font-size:0.65rem;letter-spacing:0.15em;color:#4A5568;text-transform:uppercase;margin-bottom:0.75rem;">Summary</div>'
            f'<div style="font-size:0.9rem;line-height:1.8;color:#A8B4CC;">{report.get("summary", "")}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with hero_r:
        st.markdown(
            f'<div class="iq-card" style="height:100%;">'
            f'<div style="font-size:0.65rem;letter-spacing:0.15em;color:#4A5568;text-transform:uppercase;margin-bottom:0.75rem;">Stats</div>'
            f'<table style="width:100%;font-size:0.82rem;border-collapse:collapse;">'
            f'<tr><td style="color:#4A5568;padding:0.3rem 0;">Questions answered</td>'
            f'<td style="color:#D4D9E8;text-align:right;">{len(st.session_state.scores)}</td></tr>'
            f'<tr><td style="color:#4A5568;padding:0.3rem 0;">Hints used</td>'
            f'<td style="color:#D4D9E8;text-align:right;">{st.session_state.hints_used}</td></tr>'
            f'<tr><td style="color:#4A5568;padding:0.3rem 0;">Skipped</td>'
            f'<td style="color:#D4D9E8;text-align:right;">{st.session_state.skips_used}</td></tr>'
            f'<tr><td style="color:#4A5568;padding:0.3rem 0;">Avg answer time</td>'
            f'<td style="color:#D4D9E8;text-align:right;">{avg_time:.0f}s</td></tr>'
            f'</table>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown('<hr style="margin:2rem 0;">', unsafe_allow_html=True)

    # ── Strengths & Weaknesses ────────────────────────────────────────────────
    sw_l, sw_r = st.columns(2, gap="large")
    with sw_l:
        st.markdown('<h3 style="margin-bottom:1rem;">Strengths</h3>', unsafe_allow_html=True)
        for s in report.get("strengths", []):
            st.markdown(
                f'<div class="iq-card iq-card-accent">'
                f'<span style="color:#00E5B4;font-size:0.7rem;letter-spacing:0.1em;">✦ STRENGTH</span>'
                f'<div style="margin-top:0.5rem;font-size:0.875rem;color:#C8CDD8;line-height:1.7;">{s}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
    with sw_r:
        st.markdown('<h3 style="margin-bottom:1rem;">Areas to Improve</h3>', unsafe_allow_html=True)
        for w in report.get("weak_areas", []):
            st.markdown(
                f'<div class="iq-card iq-card-danger">'
                f'<span style="color:#FF5252;font-size:0.7rem;letter-spacing:0.1em;">△ IMPROVE</span>'
                f'<div style="margin-top:0.5rem;font-size:0.875rem;color:#C8CDD8;line-height:1.7;">{w}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    if report.get("top_tip"):
        st.markdown(
            f'<div class="iq-card iq-card-warn">'
            f'<span style="color:#F5A623;font-size:0.7rem;letter-spacing:0.1em;">◈ TOP TIP</span>'
            f'<div style="margin-top:0.5rem;font-size:0.875rem;color:#C8CDD8;line-height:1.7;">{report["top_tip"]}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown('<hr style="margin:2rem 0;">', unsafe_allow_html=True)

    # ── Charts ────────────────────────────────────────────────────────────────
    if st.session_state.scores:
        c1, c2 = st.columns(2, gap="large")
        with c1:
            st.plotly_chart(
                score_timeline_chart(st.session_state.scores, st.session_state.confidence_scores),
                use_container_width=True,
            )
        with c2:
            if avg_dims:
                st.plotly_chart(radar_chart(avg_dims), use_container_width=True)

        c3, c4 = st.columns(2, gap="large")
        with c3:
            st.plotly_chart(per_question_bar(st.session_state.scores), use_container_width=True)
        with c4:
            if st.session_state.answer_times:
                st.plotly_chart(answer_time_chart(st.session_state.answer_times),
                                use_container_width=True)

        star_fig = star_donut_chart(st.session_state.star_results)
        if star_fig:
            sc, _ = st.columns([1, 1])
            with sc:
                st.plotly_chart(star_fig, use_container_width=True)

    st.markdown('<hr style="margin:2rem 0;">', unsafe_allow_html=True)

    # ── Actions ───────────────────────────────────────────────────────────────
    act1, act2, act3 = st.columns(3)
    with act1:
        if st.button("↩ Try Another Topic", use_container_width=True):
            reset_interview()
            st.session_state.step = "topics"
            st.rerun()
    with act2:
        if st.button("⚙ New Configuration", use_container_width=True):
            reset_interview()
            st.session_state.step = "configure"
            st.rerun()
    with act3:
        st.markdown('<div class="btn-primary">', unsafe_allow_html=True)
        if st.button("→ Start Fresh", use_container_width=True):
            reset_full()
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
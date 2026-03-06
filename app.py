"""
app.py — InterviewIQ
Clean build: no voice module, hint bug fixed, full legibility + theme consistency.
"""

import os
import streamlit as st
import time

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
# SESSION + THEME INIT
# ══════════════════════════════════════════════════════════════════════════════
init_session()

if "theme" not in st.session_state:
    st.session_state.theme = "dark"

T = st.session_state.theme   # "dark" | "light"

# ══════════════════════════════════════════════════════════════════════════════
# DESIGN TOKENS
# Every colour in the app is sourced from here — no hardcoded hex anywhere else.
# ══════════════════════════════════════════════════════════════════════════════
if T == "dark":
    BG          = "#07090E"
    BG_CARD     = "#0D1220"
    BG_INPUT    = "#0D1220"
    BG_BOT      = "#0D1220"
    BG_USER     = "#111B2E"
    BORDER      = "#1C2840"
    BORDER_HI   = "#2C3F60"
    TEXT_HEAD   = "#F0F3FC"
    TEXT_BODY   = "#C2CEDF"
    TEXT_SUB    = "#728096"
    TEXT_MUTED  = "#334055"
    ACCENT      = "#00E5B4"
    WARN        = "#F5A623"
    DANGER      = "#FF5555"
    INFO        = "#6B9FFF"
    SCROLLBAR   = "#1C2840"
    BTN_BG      = "#0D1220"
    BTN_TEXT    = "#C2CEDF"
    LOGO_BASE   = "#728096"
    STEP_DONE   = "#003D2F"
    RADIO_BG    = "#0D1220"
else:
    BG          = "#F0F2F8"
    BG_CARD     = "#FFFFFF"
    BG_INPUT    = "#FFFFFF"
    BG_BOT      = "#FFFFFF"
    BG_USER     = "#E8EEFF"
    BORDER      = "#C8D4E8"
    BORDER_HI   = "#8FA8CC"
    TEXT_HEAD   = "#080E22"
    TEXT_BODY   = "#18253D"
    TEXT_SUB    = "#3D5270"
    TEXT_MUTED  = "#8FA8C0"
    ACCENT      = "#007A5E"
    WARN        = "#8A4A00"
    DANGER      = "#A8101C"
    INFO        = "#1A3E8A"
    SCROLLBAR   = "#C8D4E8"
    BTN_BG      = "#FFFFFF"
    BTN_TEXT    = "#18253D"
    LOGO_BASE   = "#8FA8C0"
    STEP_DONE   = "#A8E8D8"
    RADIO_BG    = "#FFFFFF"

# ══════════════════════════════════════════════════════════════════════════════
# CSS
# Uses !important pervasively to override Streamlit's own stylesheet.
# Covers every surface that Streamlit renders: native widgets, markdown,
# chat input, expanders, metrics, alerts — so theme switching is complete.
# ══════════════════════════════════════════════════════════════════════════════
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=JetBrains+Mono:wght@300;400;500;600&display=swap');

/* ── Global reset ─────────────────────────────────────────────── */
*, *::before, *::after {{ box-sizing: border-box; }}

html, body, .stApp, [class*="css"],
[data-testid="stAppViewContainer"],
[data-testid="stAppViewBlockContainer"],
[data-testid="stVerticalBlock"],
[data-testid="stHorizontalBlock"],
[data-testid="column"],
.main, .element-container {{
    background-color: {BG} !important;
    color: {TEXT_BODY} !important;
    font-family: 'JetBrains Mono', monospace !important;
}}

/* ── Hide Streamlit chrome ────────────────────────────────────── */
#MainMenu, footer, header,
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="collapsedControl"],
section[data-testid="stSidebar"] {{ display: none !important; }}

/* ── Layout ───────────────────────────────────────────────────── */
.block-container {{
    max-width: 1120px !important;
    padding: 2.5rem 2.5rem 5rem !important;
    background-color: {BG} !important;
}}

/* ── All text elements ────────────────────────────────────────── */
p, span, div, li, td, th, label, caption, small,
[data-testid="stText"],
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] span,
[data-testid="stMarkdownContainer"] li {{
    color: {TEXT_BODY} !important;
}}

/* ── Headings ─────────────────────────────────────────────────── */
h1, h2,
[data-testid="stMarkdownContainer"] h1,
[data-testid="stMarkdownContainer"] h2 {{
    font-family: 'Instrument Serif', serif !important;
    color: {TEXT_HEAD} !important;
    font-weight: 400 !important;
    letter-spacing: -0.02em;
    line-height: 1.15;
}}
h3, h4,
[data-testid="stMarkdownContainer"] h3,
[data-testid="stMarkdownContainer"] h4 {{
    font-family: 'JetBrains Mono', monospace !important;
    color: {TEXT_HEAD} !important;
    font-weight: 600 !important;
    font-size: 0.72rem !important;
    letter-spacing: 0.14em !important;
    text-transform: uppercase !important;
}}
.stCaption, [data-testid="stCaption"],
[data-testid="stCaptionContainer"] {{
    color: {TEXT_SUB} !important;
    font-size: 0.74rem !important;
}}

/* ── HR ───────────────────────────────────────────────────────── */
hr {{ border: none !important; border-top: 1px solid {BORDER} !important; margin: 1.75rem 0; }}

/* ── Cards (custom) ───────────────────────────────────────────── */
.iq-card {{
    background: {BG_CARD} !important;
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 1.4rem 1.6rem;
    margin-bottom: 1rem;
    color: {TEXT_BODY} !important;
    transition: border-color 0.2s ease;
}}
.iq-card * {{ color: inherit; }}
.iq-card:hover {{ border-color: {BORDER_HI}; }}
.iq-card-accent {{ border-left: 3px solid {ACCENT} !important; }}
.iq-card-warn   {{ border-left: 3px solid {WARN}   !important; }}
.iq-card-danger {{ border-left: 3px solid {DANGER} !important; }}

/* ── Chat bubbles ─────────────────────────────────────────────── */
.bubble-wrap {{ display:flex; flex-direction:column; gap:1.25rem; margin-bottom:1.5rem; }}

.bubble-bot {{ display:flex; gap:0.875rem; align-items:flex-start; max-width:84%; }}
.bubble-bot-avatar {{
    width:32px; height:32px; min-width:32px;
    background:{ACCENT}; color:{BG};
    border-radius:4px; flex-shrink:0; margin-top:2px;
    display:flex; align-items:center; justify-content:center;
    font-size:10px; font-weight:700; letter-spacing:0.04em;
}}
.bubble-bot-body {{
    background:{BG_BOT}; border:1px solid {BORDER};
    border-radius:2px 8px 8px 8px;
    padding:1rem 1.3rem; line-height:1.8;
    font-size:0.9rem; color:{TEXT_BODY} !important;
}}

.bubble-user {{ display:flex; gap:0.875rem; align-items:flex-start; max-width:84%; margin-left:auto; flex-direction:row-reverse; }}
.bubble-user-avatar {{
    width:32px; height:32px; min-width:32px;
    background:{BG_USER}; border:1px solid {BORDER}; color:{TEXT_SUB};
    border-radius:4px; flex-shrink:0; margin-top:2px;
    display:flex; align-items:center; justify-content:center;
    font-size:10px; font-weight:700; letter-spacing:0.04em;
}}
.bubble-user-body {{
    background:{BG_USER}; border:1px solid {BORDER};
    border-radius:8px 2px 8px 8px;
    padding:1rem 1.3rem; line-height:1.8;
    font-size:0.9rem; color:{TEXT_BODY} !important;
}}
.feedback-card {{
    background:{BG_CARD}; border:1px solid {ACCENT}38;
    border-radius:6px; padding:1.1rem 1.4rem;
    margin-top:0.75rem; line-height:1.85;
    font-size:0.875rem; color:{TEXT_BODY} !important;
}}
.feedback-card * {{ color:{TEXT_BODY} !important; }}

/* ── Pills ────────────────────────────────────────────────────── */
.pill {{
    display:inline-flex; align-items:center;
    padding:0.22rem 0.72rem; border-radius:3px;
    font-size:0.7rem; font-weight:700;
    letter-spacing:0.07em; margin:0.15rem;
    border:1px solid; text-transform:uppercase;
}}
.pill-green {{ color:{ACCENT};  border-color:{ACCENT}55; background:{ACCENT}18; }}
.pill-amber {{ color:{WARN};    border-color:{WARN}55;   background:{WARN}18; }}
.pill-red   {{ color:{DANGER};  border-color:{DANGER}55; background:{DANGER}18; }}
.pill-blue  {{ color:{INFO};    border-color:{INFO}55;   background:{INFO}18; }}

/* ── Score hero ───────────────────────────────────────────────── */
.score-hero {{
    font-family:'Instrument Serif',serif;
    font-size:5rem; color:{ACCENT}; line-height:1; font-weight:400;
}}
.score-label {{
    font-size:0.62rem; letter-spacing:0.2em; text-transform:uppercase;
    color:{TEXT_SUB}; margin-top:0.3rem;
}}

/* ── Progress bar ─────────────────────────────────────────────── */
.stProgress > div > div > div > div {{
    background:linear-gradient(90deg,{ACCENT},{INFO}) !important;
    border-radius:0 !important;
}}
.stProgress > div > div {{
    background:{BORDER} !important; border-radius:0 !important; height:3px !important;
}}

/* ── Text inputs & textareas ──────────────────────────────────── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {{
    background:{BG_INPUT} !important;
    border:1px solid {BORDER} !important;
    border-radius:5px !important;
    color:{TEXT_BODY} !important;
    font-family:'JetBrains Mono',monospace !important;
    font-size:13px !important;
    caret-color:{ACCENT} !important;
}}
.stTextInput > div > div > input::placeholder,
.stTextArea > div > div > textarea::placeholder {{
    color:{TEXT_SUB} !important; opacity:1 !important;
}}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {{
    border-color:{ACCENT} !important;
    box-shadow:0 0 0 2px {ACCENT}22 !important;
    outline:none !important;
}}
/* Input labels */
.stTextInput label, .stTextArea label,
[data-testid="stWidgetLabel"] p,
[data-testid="stWidgetLabel"] span {{
    color:{TEXT_BODY} !important;
    font-size:0.8rem !important;
    font-weight:500 !important;
}}

/* ── File uploader ────────────────────────────────────────────── */
[data-testid="stFileUploader"] {{
    background:{BG_CARD} !important;
    border-radius:6px !important;
}}
[data-testid="stFileUploader"] > div,
[data-testid="stFileUploaderDropzone"] {{
    background:{BG_INPUT} !important;
    border:2px dashed {BORDER_HI} !important;
    border-radius:6px !important;
}}
[data-testid="stFileUploader"] * {{ color:{TEXT_BODY} !important; }}
[data-testid="stFileUploader"] small {{ color:{TEXT_SUB} !important; }}
[data-testid="stFileUploaderDropzone"]:hover {{ border-color:{ACCENT} !important; }}

/* ── Selectbox ────────────────────────────────────────────────── */
[data-baseweb="select"] > div {{
    background:{BG_INPUT} !important;
    border-color:{BORDER} !important;
    color:{TEXT_BODY} !important;
}}
[data-baseweb="select"] * {{ color:{TEXT_BODY} !important; }}

/* ── Slider ───────────────────────────────────────────────────── */
.stSlider > div > div > div > div {{ background:{ACCENT} !important; }}
[data-testid="stTickBar"] > div {{ color:{TEXT_SUB} !important; }}
[data-testid="stSliderThumbValue"] {{
    color:{TEXT_HEAD} !important; background:{BG_CARD} !important;
    border:1px solid {BORDER} !important;
}}

/* ── Buttons ──────────────────────────────────────────────────── */
.stButton > button {{
    background:{BTN_BG} !important;
    border:1px solid {BORDER} !important;
    color:{BTN_TEXT} !important;
    border-radius:5px !important;
    font-family:'JetBrains Mono',monospace !important;
    font-size:12px !important; letter-spacing:0.05em !important;
    padding:0.55rem 1.1rem !important; font-weight:500 !important;
    transition:all 0.15s ease !important;
}}
.stButton > button:hover {{
    border-color:{ACCENT} !important;
    color:{ACCENT} !important;
    background:{ACCENT}12 !important;
}}
.stButton > button:disabled {{
    opacity:0.4 !important; cursor:not-allowed !important;
}}
.btn-primary > button {{
    background:{ACCENT} !important; border:1px solid {ACCENT} !important;
    color:{BG} !important; font-weight:700 !important; letter-spacing:0.07em !important;
}}
.btn-primary > button:hover {{ opacity:0.88 !important; color:{BG} !important; }}
.btn-danger > button {{
    border-color:{DANGER}55 !important; color:{DANGER} !important;
    background:{BG_CARD} !important;
}}
.btn-danger > button:hover {{
    border-color:{DANGER} !important; background:{DANGER}12 !important; color:{DANGER} !important;
}}

/* ── Radio buttons ────────────────────────────────────────────── */
.stRadio > div {{ gap:0.5rem !important; }}
.stRadio > div > label {{
    background:{RADIO_BG} !important;
    border:1px solid {BORDER} !important;
    border-radius:5px !important;
    padding:0.7rem 1.1rem !important;
    color:{TEXT_BODY} !important;
    cursor:pointer; transition:all 0.15s ease;
}}
.stRadio > div > label > div > p,
.stRadio > div > label span {{
    color:{TEXT_BODY} !important;
}}
.stRadio > div > label:hover {{
    border-color:{BORDER_HI} !important; color:{TEXT_HEAD} !important;
}}
.stRadio > div > label[data-checked="true"],
.stRadio > div > label[aria-checked="true"] {{
    border-color:{ACCENT} !important;
    background:{ACCENT}15 !important;
    color:{ACCENT} !important;
}}
.stRadio > div > label[data-checked="true"] span,
.stRadio > div > label[aria-checked="true"] span,
.stRadio > div > label[data-checked="true"] p,
.stRadio > div > label[aria-checked="true"] p {{
    color:{ACCENT} !important;
}}
/* Radio dot circle */
.stRadio [data-baseweb="radio"] div[role="radio"] {{
    border-color:{BORDER_HI} !important;
}}
.stRadio [data-baseweb="radio"] div[role="radio"][aria-checked="true"] {{
    border-color:{ACCENT} !important; background:{ACCENT} !important;
}}

/* ── Expander ─────────────────────────────────────────────────── */
[data-testid="stExpander"] {{
    background:{BG_CARD} !important;
    border:1px solid {BORDER} !important;
    border-radius:5px !important;
}}
[data-testid="stExpander"] summary {{
    color:{TEXT_BODY} !important;
    background:{BG_CARD} !important;
}}
[data-testid="stExpander"] summary:hover {{ color:{TEXT_HEAD} !important; }}
[data-testid="stExpander"] summary svg {{ fill:{TEXT_SUB} !important; }}
[data-testid="stExpander"] > div {{
    background:{BG_CARD} !important; color:{TEXT_BODY} !important;
}}

/* ── Metrics ──────────────────────────────────────────────────── */
[data-testid="stMetric"] {{ background:{BG_CARD} !important; }}
[data-testid="stMetricValue"] {{
    font-family:'Instrument Serif',serif !important;
    color:{TEXT_HEAD} !important; font-size:2rem !important;
}}
[data-testid="stMetricLabel"] {{
    color:{TEXT_SUB} !important;
    font-size:0.68rem !important; letter-spacing:0.1em !important;
    text-transform:uppercase !important;
}}
[data-testid="stMetricDelta"] {{ color:{ACCENT} !important; }}

/* ── Alerts (success / error / warning / info) ────────────────── */
[data-testid="stAlert"] {{
    background:{BG_CARD} !important;
    border-radius:5px !important;
    color:{TEXT_BODY} !important;
}}
[data-testid="stAlert"] * {{ color:{TEXT_BODY} !important; }}
.stSuccess {{ background:{ACCENT}12 !important; border:1px solid {ACCENT}44 !important; }}
.stError   {{ background:{DANGER}12 !important; border:1px solid {DANGER}44 !important; }}
.stWarning {{ background:{WARN}12   !important; border:1px solid {WARN}44   !important; }}
.stInfo    {{ background:{INFO}12   !important; border:1px solid {INFO}44   !important; }}

/* ── Code blocks ──────────────────────────────────────────────── */
.stCodeBlock, [data-testid="stCodeBlock"] {{
    background:{BG_CARD} !important;
    border:1px solid {BORDER} !important;
    border-radius:5px !important;
}}
code, .stCode code {{ color:{ACCENT} !important; font-size:0.82rem !important; }}
pre, pre code {{ color:{TEXT_BODY} !important; background:{BG_CARD} !important; }}

/* ── Chat input ───────────────────────────────────────────────── */
[data-testid="stChatInput"],
[data-testid="stChatInputContainer"] {{
    background:{BG} !important;
    border-top:1px solid {BORDER} !important;
}}
[data-testid="stChatInput"] > div,
[data-testid="stChatInputContainer"] > div {{
    background:{BG_INPUT} !important;
    border:1px solid {BORDER} !important;
    border-radius:5px !important;
}}
[data-testid="stChatInput"] textarea,
[data-testid="stChatInputContainer"] textarea {{
    color:{TEXT_BODY} !important;
    background:{BG_INPUT} !important;
    font-family:'JetBrains Mono',monospace !important;
}}
[data-testid="stChatInput"] textarea::placeholder {{ color:{TEXT_SUB} !important; }}
[data-testid="stChatInputSubmitButton"] button {{
    background:{ACCENT} !important; border:none !important; color:{BG} !important;
}}

/* ── Spinner ──────────────────────────────────────────────────── */
.stSpinner > div {{ border-top-color:{ACCENT} !important; }}

/* ── Scrollbar ────────────────────────────────────────────────── */
::-webkit-scrollbar {{ width:4px; height:4px; }}
::-webkit-scrollbar-track {{ background:{BG}; }}
::-webkit-scrollbar-thumb {{ background:{SCROLLBAR}; border-radius:2px; }}
::-webkit-scrollbar-thumb:hover {{ background:{BORDER_HI}; }}

/* ── Topic card (custom) ──────────────────────────────────────── */
.topic-card {{
    background:{BG_CARD}; border:1px solid {BORDER};
    border-radius:6px; padding:1.5rem 1rem;
    text-align:center; transition:all 0.2s ease;
    color:{TEXT_BODY} !important;
}}
.topic-card:hover {{ border-color:{ACCENT}; background:{ACCENT}0A; }}
.topic-number {{
    font-size:0.58rem; letter-spacing:0.2em; color:{ACCENT};
    text-transform:uppercase; margin-bottom:0.5rem; font-weight:700;
}}
.topic-name {{
    font-size:0.875rem; font-weight:500;
    color:{TEXT_HEAD}; line-height:1.4;
}}

/* ── Logo ─────────────────────────────────────────────────────── */
.iq-logo {{
    font-family:'Instrument Serif',serif; font-size:1.05rem;
    /* base part of name uses logo base token */
    color:{LOGO_BASE}; letter-spacing:0.02em;
}}
.iq-logo span {{ color:{ACCENT}; }}

/* ── Step progress bar ────────────────────────────────────────── */
.step-bar {{ display:flex; gap:5px; margin-bottom:2.5rem; }}
.step-dot {{
    height:3px; flex:1; border-radius:1px;
    background:{BORDER}; transition:background 0.3s ease;
}}
.step-dot.active {{ background:{ACCENT}; }}
.step-dot.done   {{ background:{STEP_DONE}; }}

/* ── Columns gap fix ──────────────────────────────────────────── */
[data-testid="column"] {{ background:{BG} !important; }}
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# API KEY — .env → st.secrets → hard stop
# ══════════════════════════════════════════════════════════════════════════════
api_key = os.environ.get("GEMINI_API_KEY", "")
if not api_key:
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
    except Exception:
        pass

if not api_key:
    st.markdown(f"""
    <div style="max-width:520px;margin:8rem auto;text-align:center;">
      <div style="font-family:'Instrument Serif',serif;font-size:2.2rem;
                  color:{TEXT_HEAD};margin-bottom:1rem;">Missing API Key</div>
      <div style="color:{TEXT_SUB};font-size:0.85rem;line-height:2.1;">
        Create a <code style="color:{ACCENT}">.env</code> file in the project root:<br><br>
        <code style="background:{BG_CARD};border:1px solid {BORDER};padding:0.5rem 1.4rem;
                     display:inline-block;border-radius:5px;color:{ACCENT};margin-top:0.3rem;">
          GEMINI_API_KEY=your_key_here
        </code><br><br>
        Then restart with <code style="color:{ACCENT}">streamlit run app.py</code>
      </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

init_gemini(api_key)


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════
def step_bar(current: int, total: int = 5):
    dots = "".join(
        f'<div class="step-dot {"active" if i == current else "done" if i < current else ""}"></div>'
        for i in range(1, total + 1)
    )
    st.markdown(f'<div class="step-bar">{dots}</div>', unsafe_allow_html=True)


def topbar():
    c_logo, _, c_toggle = st.columns([3, 5, 2])
    with c_logo:
        st.markdown(
            f'<div class="iq-logo" style="padding-top:5px;">Interview<span>IQ</span></div>',
            unsafe_allow_html=True,
        )
    with c_toggle:
        icon = "⚪️  Light" if T == "dark" else "⚫️  Dark"
        if st.button(icon, key="theme_btn"):
            st.session_state.theme = "light" if T == "dark" else "dark"
            st.rerun()


def sec_label(text: str, color: str = None):
    st.markdown(
        f'<div style="font-size:0.62rem;letter-spacing:0.2em;'
        f'color:{color or TEXT_SUB};text-transform:uppercase;'
        f'font-weight:700;margin-bottom:0.65rem;">{text}</div>',
        unsafe_allow_html=True,
    )


def sys_prompt_from_state() -> str:
    return build_system_prompt(
        company=st.session_state.company,
        role=st.session_state.role,
        persona=st.session_state.persona,
        difficulty=st.session_state.difficulty,
        resume_text=st.session_state.resume_text,
        jd=st.session_state.jd,
        num_questions=st.session_state.num_questions,
    )


# ══════════════════════════════════════════════════════════════════════════════
# STEP 1 — INPUT
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.step == "input":

    topbar()
    step_bar(1)

    st.markdown(f"""
    <h1 style="font-size:3rem;margin-bottom:0.3rem;">
        Your next role<br><em>starts here.</em>
    </h1>
    <p style="color:{TEXT_SUB};margin-bottom:2.5rem;font-size:0.85rem;letter-spacing:0.02em;">
        AI mock interviews — tailored to your resume and target role.
    </p>
    """, unsafe_allow_html=True)

    col_l, sp, col_r = st.columns([5, 1, 5])

    with col_l:
        sec_label("01 / Your Resume")
        resume_file = st.file_uploader(
            "Upload resume (PDF or DOCX)",
            type=["pdf", "docx"],
            help="Text extracted locally — never stored.",
        )
        if resume_file:
            resume_text, err = parse_uploaded_file(resume_file)
            if err:
                st.error(err)
            else:
                st.session_state.resume_text = resume_text
                st.markdown(
                    f'<div class="pill pill-green" style="margin-bottom:0.5rem;">'
                    f'✓ {len(resume_text):,} chars extracted</div>',
                    unsafe_allow_html=True,
                )
                with st.expander("Preview extracted text"):
                    st.code(
                        resume_text[:700] + ("…" if len(resume_text) > 700 else ""),
                        language=None,
                    )

    with col_r:
        sec_label("02 / Role Details")
        st.session_state.company = st.text_input(
            "Company name",
            value=st.session_state.company,
            placeholder="e.g. Google, Stripe, Anthropic…",
        )
        st.session_state.role = st.text_input(
            "Target role",
            value=st.session_state.role,
            placeholder="e.g. Senior Backend Engineer, PM…",
        )
        st.session_state.jd = st.text_area(
            "Job description",
            value=st.session_state.jd,
            placeholder="Paste the full job description here…",
            height=180,
        )

    st.markdown("<br>", unsafe_allow_html=True)
    can_proceed = bool(
        st.session_state.company.strip() and
        st.session_state.role.strip() and
        st.session_state.jd.strip()
    )
    _, c2, _ = st.columns([2, 3, 2])
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
                f'<p style="text-align:center;color:{TEXT_SUB};font-size:0.74rem;margin-top:0.5rem;">'
                f'Company, Role and Job Description are required.</p>',
                unsafe_allow_html=True,
            )


# ══════════════════════════════════════════════════════════════════════════════
# STEP 2 — CONFIGURE
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.step == "configure":

    topbar()
    step_bar(2)
    st.markdown('<h1>Configure<br><em>your session.</em></h1>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    col_a, sp, col_b = st.columns([5, 1, 5])

    with col_a:
        sec_label("Difficulty")
        chosen_diff = st.radio(
            "Difficulty", DIFFICULTY_OPTIONS,
            index=DIFFICULTY_OPTIONS.index(st.session_state.difficulty),
            label_visibility="collapsed",
        )
        st.session_state.difficulty = chosen_diff
        st.markdown(
            f'<div class="iq-card iq-card-accent" style="margin-top:0.75rem;">'
            f'<span style="color:{TEXT_BODY};font-size:0.83rem;line-height:1.75;">'
            f'{DIFFICULTY_DESCRIPTIONS[chosen_diff]}</span></div>',
            unsafe_allow_html=True,
        )
        st.markdown('<div style="height:1.5rem;"></div>', unsafe_allow_html=True)
        sec_label("Number of Questions")
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
        sec_label("Interviewer Persona")
        chosen_persona = st.radio(
            "Persona", PERSONA_OPTIONS,
            index=PERSONA_OPTIONS.index(st.session_state.persona),
            label_visibility="collapsed",
        )
        st.session_state.persona = chosen_persona
        st.markdown(
            f'<div class="iq-card iq-card-accent" style="margin-top:0.75rem;">'
            f'<span style="color:{TEXT_BODY};font-size:0.83rem;line-height:1.75;">'
            f'{PERSONA_DESCRIPTIONS[chosen_persona]}</span></div>',
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
                st.session_state.system_prompt = sys_prompt_from_state()
                st.session_state.step = "topics"
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# STEP 3 — TOPIC SELECTION
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.step == "topics":

    topbar()
    step_bar(3)
    st.markdown('<h1>Pick your<br><em>battleground.</em></h1>', unsafe_allow_html=True)
    st.markdown(
        f'<p style="color:{TEXT_SUB};font-size:0.83rem;margin-bottom:2rem;">'
        f'{st.session_state.role} · {st.session_state.company} · '
        f'{st.session_state.difficulty} · {st.session_state.persona}</p>',
        unsafe_allow_html=True,
    )

    cols = st.columns(len(st.session_state.topics), gap="small")
    for i, topic in enumerate(st.session_state.topics):
        with cols[i]:
            st.markdown(
                f'<div class="topic-card">'
                f'<div class="topic-number">0{i + 1}</div>'
                f'<div class="topic-name">{topic}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
            if st.button("Start →", key=f"topic_{i}", use_container_width=True):
                reset_interview()
                st.session_state.current_topic = topic
                st.session_state.system_prompt = sys_prompt_from_state()
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

    # ── Header ────────────────────────────────────────────────────────────────
    hdr_l, hdr_m, hdr_r = st.columns([4, 3, 2])
    with hdr_l:
        topbar()
        st.markdown(
            f'<span style="color:{TEXT_SUB};font-size:0.74rem;">'
            f'{st.session_state.current_topic} · {st.session_state.persona} · '
            f'{st.session_state.difficulty}</span>',
            unsafe_allow_html=True,
        )
    with hdr_m:
        progress = (st.session_state.question_number / st.session_state.num_questions
                    if st.session_state.num_questions else 0)
        st.markdown(
            f'<div style="font-size:0.68rem;color:{TEXT_SUB};letter-spacing:0.1em;'
            f'text-transform:uppercase;margin-bottom:5px;">'
            f'Question {st.session_state.question_number} of {st.session_state.num_questions}'
            f'</div>',
            unsafe_allow_html=True,
        )
        st.progress(min(progress, 1.0))
    with hdr_r:
        avg_so_far = (sum(st.session_state.scores) / len(st.session_state.scores)
                      if st.session_state.scores else 0)
        st.markdown(
            f'<div style="text-align:right;padding-top:4px;">'
            f'<span style="font-family:Instrument Serif,serif;font-size:1.6rem;color:{ACCENT};">'
            f'{avg_so_far:.1f}</span>'
            f'<span style="color:{TEXT_SUB};font-size:0.7rem;"> / 10 avg</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown(f'<hr style="margin:0.75rem 0 1.5rem;">', unsafe_allow_html=True)

    # ── Generate first question ───────────────────────────────────────────────
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

    # ── Chat history ──────────────────────────────────────────────────────────
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
                f'<div class="bubble-user-avatar">YOU</div>'
                f'<div class="bubble-user-body">{msg["content"]}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
    st.markdown("</div>", unsafe_allow_html=True)

    # ── Controls: Hint | Skip ─────────────────────────────────────────────────
    hint_col, skip_col, _ = st.columns([1.2, 1.2, 5.6])

    with hint_col:
        st.markdown('<div class="btn-danger">', unsafe_allow_html=True)
        hint_clicked = st.button(
            "💡 Hint", key="hint_btn", use_container_width=True,
            help=f"Get a nudge — costs {HINT_PENALTY} pt",
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with skip_col:
        st.markdown('<div class="btn-danger">', unsafe_allow_html=True)
        skip_clicked = st.button(
            "⏭ Skip", key="skip_btn", use_container_width=True,
            help="Skip this question — tracked in your report",
        )
        st.markdown("</div>", unsafe_allow_html=True)

    # ── Hint logic ────────────────────────────────────────────────────────────
    if hint_clicked:
        with st.spinner("Generating hint…"):
            # ✅ FIX: generate_hint takes only hint_prompt — system_prompt
            #         is already baked into build_hint_prompt via the module.
            #         Pass just the one string it expects.
            hint_text = generate_hint(
                build_hint_prompt(
                    st.session_state.current_question,
                    st.session_state.current_topic,
                )
            )
        st.session_state.hints_used += 1
        st.markdown(
            f'<div class="iq-card iq-card-warn">'
            f'<div style="font-size:0.62rem;letter-spacing:0.18em;color:{WARN};'
            f'font-weight:700;text-transform:uppercase;margin-bottom:0.5rem;">Hint</div>'
            f'<div style="color:{TEXT_BODY};font-size:0.875rem;line-height:1.8;">{hint_text}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # ── Skip logic ────────────────────────────────────────────────────────────
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
        push_chat(
            "user",
            f'<span style="color:{TEXT_MUTED};font-style:italic;font-size:0.85rem;">'
            f'— skipped —</span>',
        )

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
    user_answer = st.chat_input("Type your answer here…")

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

        score_cls = "pill-green" if score >= 7 else ("pill-amber" if score >= 5 else "pill-red")
        conf_cls  = "pill-green" if local_conf >= 65 else ("pill-amber" if local_conf >= 40 else "pill-red")

        star_badge = ""
        if star_info.get("used_star") is True:
            star_badge = '<span class="pill pill-green">✓ STAR</span>'
        elif star_info.get("used_star") is False:
            missing = ", ".join(star_info.get("missing", []))
            star_badge = f'<span class="pill pill-amber">⚠ STAR: missing {missing}</span>'

        feedback_html = (
            f'<div class="feedback-card">'
            f'<div style="margin-bottom:0.8rem;">'
            f'<span class="pill {score_cls}">Score {score}/10</span>'
            f'<span class="pill {conf_cls}">Confidence {local_conf}%</span>'
            f'<span class="pill pill-blue">⏱ {elapsed}s</span>'
            f'{star_badge}</div>'
            f'<div style="color:{TEXT_BODY};font-size:0.875rem;line-height:1.85;">'
            f'{feedback}</div>'
            f'</div>'
        )

        next_q = result.get("next_question")
        is_last = (
            st.session_state.question_number >= st.session_state.num_questions
            or result.get("is_last", False)
            or not next_q
        )

        if is_last:
            push_chat(
                "assistant",
                feedback_html +
                f'<br><div style="color:{ACCENT};font-size:0.85rem;margin-top:0.5rem;">'
                f'✓ Interview complete — generating your report.</div>',
            )
            st.session_state.step = "report"
        else:
            st.session_state.question_number += 1
            push_chat(
                "assistant",
                feedback_html +
                f'<br><div style="margin-top:1.1rem;color:{TEXT_HEAD};'
                f'font-size:0.9rem;font-weight:500;line-height:1.75;">{next_q}</div>',
            )
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

    report   = st.session_state.report
    topbar()
    step_bar(5)

    grade     = ("Excellent" if overall >= 8 else "Good" if overall >= 6
                 else "Needs Work" if overall >= 4 else "Keep Practising")
    grade_col = (ACCENT if overall >= 8 else INFO if overall >= 6
                 else WARN if overall >= 4 else DANGER)
    avg_time  = (sum(st.session_state.answer_times) / len(st.session_state.answer_times)
                 if st.session_state.answer_times else 0)

    st.markdown(
        f'<h1 style="margin-bottom:0.3rem;">Session<br><em>complete.</em></h1>'
        f'<p style="color:{TEXT_SUB};font-size:0.82rem;margin-bottom:2.5rem;">'
        f'{st.session_state.role} · {st.session_state.company} · '
        f'{st.session_state.current_topic}</p>',
        unsafe_allow_html=True,
    )

    hero_l, hero_m, hero_r = st.columns([2, 4, 3])
    with hero_l:
        st.markdown(
            f'<div class="iq-card" style="text-align:center;padding:2rem 1rem;">'
            f'<div class="score-hero">{overall:.1f}</div>'
            f'<div class="score-label">overall score</div>'
            f'<div style="margin-top:0.8rem;font-size:0.82rem;font-weight:700;'
            f'color:{grade_col};">{grade}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with hero_m:
        st.markdown(
            f'<div class="iq-card" style="height:100%;">'
            f'<div style="font-size:0.62rem;letter-spacing:0.2em;color:{TEXT_SUB};'
            f'text-transform:uppercase;font-weight:700;margin-bottom:0.75rem;">Summary</div>'
            f'<div style="font-size:0.875rem;line-height:1.85;color:{TEXT_BODY};">'
            f'{report.get("summary", "")}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with hero_r:
        st.markdown(
            f'<div class="iq-card" style="height:100%;">'
            f'<div style="font-size:0.62rem;letter-spacing:0.2em;color:{TEXT_SUB};'
            f'text-transform:uppercase;font-weight:700;margin-bottom:0.75rem;">Session Stats</div>'
            f'<table style="width:100%;font-size:0.83rem;border-collapse:collapse;">'
            f'<tr><td style="color:{TEXT_SUB};padding:0.35rem 0;">Questions answered</td>'
            f'<td style="color:{TEXT_HEAD};text-align:right;font-weight:600;">{len(st.session_state.scores)}</td></tr>'
            f'<tr><td style="color:{TEXT_SUB};padding:0.35rem 0;">Hints used</td>'
            f'<td style="color:{TEXT_HEAD};text-align:right;font-weight:600;">{st.session_state.hints_used}</td></tr>'
            f'<tr><td style="color:{TEXT_SUB};padding:0.35rem 0;">Skipped</td>'
            f'<td style="color:{TEXT_HEAD};text-align:right;font-weight:600;">{st.session_state.skips_used}</td></tr>'
            f'<tr><td style="color:{TEXT_SUB};padding:0.35rem 0;">Avg answer time</td>'
            f'<td style="color:{TEXT_HEAD};text-align:right;font-weight:600;">{avg_time:.0f}s</td></tr>'
            f'</table>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown('<hr style="margin:2rem 0;">', unsafe_allow_html=True)

    sw_l, sw_r = st.columns(2, gap="large")
    with sw_l:
        sec_label("Strengths", color=ACCENT)
        for s in report.get("strengths", []):
            st.markdown(
                f'<div class="iq-card iq-card-accent">'
                f'<div style="font-size:0.6rem;letter-spacing:0.18em;color:{ACCENT};'
                f'font-weight:700;text-transform:uppercase;margin-bottom:0.45rem;">✦ Strength</div>'
                f'<div style="font-size:0.875rem;color:{TEXT_BODY};line-height:1.8;">{s}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
    with sw_r:
        sec_label("Areas to Improve", color=DANGER)
        for w in report.get("weak_areas", []):
            st.markdown(
                f'<div class="iq-card iq-card-danger">'
                f'<div style="font-size:0.6rem;letter-spacing:0.18em;color:{DANGER};'
                f'font-weight:700;text-transform:uppercase;margin-bottom:0.45rem;">△ Improve</div>'
                f'<div style="font-size:0.875rem;color:{TEXT_BODY};line-height:1.8;">{w}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    if report.get("top_tip"):
        st.markdown(
            f'<div class="iq-card iq-card-warn">'
            f'<div style="font-size:0.6rem;letter-spacing:0.18em;color:{WARN};'
            f'font-weight:700;text-transform:uppercase;margin-bottom:0.45rem;">◈ Top Tip</div>'
            f'<div style="font-size:0.875rem;color:{TEXT_BODY};line-height:1.8;">'
            f'{report["top_tip"]}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown('<hr style="margin:2rem 0;">', unsafe_allow_html=True)

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
                st.plotly_chart(
                    answer_time_chart(st.session_state.answer_times),
                    use_container_width=True,
                )

        star_fig = star_donut_chart(st.session_state.star_results)
        if star_fig:
            sc, _ = st.columns([1, 1])
            with sc:
                st.plotly_chart(star_fig, use_container_width=True)

    st.markdown('<hr style="margin:2rem 0;">', unsafe_allow_html=True)

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
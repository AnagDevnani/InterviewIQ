"""
components/dashboard.py
Renders the final interview report and visual dashboard using Plotly.
"""

import plotly.graph_objects as go
import plotly.express as px
import streamlit as st
import pandas as pd


def render_dashboard(session_state):
    """
    Main entry point. Renders the full post-interview dashboard.
    Expects session_state to have: session_log, report_data, config fields.
    """
    session_log = session_state.get("session_log", [])
    report_data = session_state.get("report_data", {})

    if not session_log:
        st.warning("No session data to display.")
        return

    answered = [item for item in session_log if not item.get("skipped", False)]
    skipped_count = session_state.get("skipped_count", 0)
    hint_count = session_state.get("hint_count", 0)

    scores = [item.get("score", 0) for item in answered]
    confidences = [item.get("local_confidence", 0) for item in answered]
    overall_score = round(sum(scores) / len(scores), 1) if scores else 0
    overall_confidence = round(sum(confidences) / len(confidences), 1) if confidences else 0

    # ── Header ────────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("## 📊 Interview Report")
    st.markdown(
        f"**Company:** {session_state.get('company', '—')} &nbsp;|&nbsp; "
        f"**Topic:** {session_state.get('current_topic', '—')} &nbsp;|&nbsp; "
        f"**Persona:** {session_state.get('persona', '—')} &nbsp;|&nbsp; "
        f"**Difficulty:** {session_state.get('difficulty', '—')}"
    )

    # ── Top KPI tiles ─────────────────────────────────────────────────────────
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Overall Score", f"{overall_score}/10")
    col2.metric("Avg Confidence", f"{overall_confidence}%")
    col3.metric("Questions Answered", len(answered))
    col4.metric("Questions Skipped", skipped_count)
    col5.metric("Hints Used", hint_count)

    st.markdown("---")

    # ── Row 1: Score trend + Confidence trend ─────────────────────────────────
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("#### 📈 Score Per Question")
        if scores:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=list(range(1, len(scores) + 1)),
                y=scores,
                mode="lines+markers",
                line=dict(color="#4F8EF7", width=2),
                marker=dict(size=8),
                name="Score",
            ))
            fig.add_hline(y=overall_score, line_dash="dot", line_color="gray",
                          annotation_text=f"Avg {overall_score}")
            fig.update_layout(
                xaxis_title="Question #",
                yaxis_title="Score",
                yaxis_range=[0, 10],
                height=300,
                margin=dict(l=20, r=20, t=20, b=20),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig, use_container_width=True)

    with col_right:
        st.markdown("#### 🧠 Confidence Trend")
        if confidences:
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(
                x=list(range(1, len(confidences) + 1)),
                y=confidences,
                mode="lines+markers",
                line=dict(color="#34C98A", width=2),
                marker=dict(size=8),
                name="Confidence",
                fill="tozeroy",
                fillcolor="rgba(52,201,138,0.1)",
            ))
            fig2.update_layout(
                xaxis_title="Question #",
                yaxis_title="Confidence %",
                yaxis_range=[0, 100],
                height=300,
                margin=dict(l=20, r=20, t=20, b=20),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig2, use_container_width=True)

    # ── Row 2: Radar chart + STAR usage ──────────────────────────────────────
    col_radar, col_star = st.columns(2)

    with col_radar:
        st.markdown("#### 🕸️ Competency Radar")
        _render_radar(session_log, overall_score, overall_confidence)

    with col_star:
        st.markdown("#### ⭐ STAR Method Usage")
        _render_star_chart(session_log)

    st.markdown("---")

    # ── Strengths & Weaknesses ────────────────────────────────────────────────
    if report_data:
        col_s, col_w = st.columns(2)
        with col_s:
            st.markdown("#### ✅ Strengths")
            for s in report_data.get("strengths", []):
                st.success(f"• {s}")
        with col_w:
            st.markdown("#### ⚠️ Areas to Improve")
            for w in report_data.get("weaknesses", []):
                st.error(f"• {w}")

        if report_data.get("overall_recommendation"):
            st.info(f"💡 **Recommendation:** {report_data['overall_recommendation']}")

    st.markdown("---")

    # ── Per-question breakdown ────────────────────────────────────────────────
    st.markdown("#### 📋 Question-by-Question Breakdown")
    for i, item in enumerate(session_log):
        label = f"Q{i+1}: {item.get('question', '')[:80]}..."
        badge = "⏭️ Skipped" if item.get("skipped") else f"Score: {item.get('score', 0)}/10"
        with st.expander(f"{label}  —  {badge}"):
            if item.get("skipped"):
                st.markdown("_This question was skipped._")
            else:
                st.markdown(f"**Your Answer:** {item.get('answer', '')}")
                st.markdown(f"**Feedback:** {item.get('feedback', '')}")
                sc = item.get("star_check", {})
                if sc.get("applicable"):
                    if sc.get("used_star"):
                        st.success("✅ STAR method detected")
                    else:
                        missing = sc.get("missing_components", [])
                        st.warning(f"⚠️ STAR incomplete — missing: {', '.join(missing)}")
                if item.get("hint_used"):
                    st.caption("🔍 Hint was used for this question")


# ── Private helpers ───────────────────────────────────────────────────────────

def _render_radar(session_log: list, overall_score: float, overall_confidence: float):
    """Build a 5-axis radar chart from session data."""
    answered = [item for item in session_log if not item.get("skipped")]

    # Technical depth: avg score of non-behavioral questions
    tech_items = [i for i in answered if not i.get("star_check", {}).get("applicable")]
    tech_score = (sum(i.get("score", 0) for i in tech_items) / len(tech_items) * 10) if tech_items else 50

    # Behavioral: avg score of behavioral questions
    beh_items = [i for i in answered if i.get("star_check", {}).get("applicable")]
    beh_score = (sum(i.get("score", 0) for i in beh_items) / len(beh_items) * 10) if beh_items else 50

    # STAR usage rate
    star_applicable = [i for i in answered if i.get("star_check", {}).get("applicable")]
    star_used = [i for i in star_applicable if i.get("star_check", {}).get("used_star")]
    star_score = (len(star_used) / len(star_applicable) * 100) if star_applicable else 70

    # Completeness (non-skipped ratio)
    total = len(session_log)
    completeness = (len(answered) / total * 100) if total else 100

    categories = ["Technical Depth", "Behavioral", "Communication\n(STAR)", "Overall Score", "Confidence"]
    values = [
        min(tech_score, 100),
        min(beh_score, 100),
        star_score,
        overall_score * 10,
        overall_confidence,
    ]
    # Close the polygon
    categories += [categories[0]]
    values += [values[0]]

    fig = go.Figure(go.Scatterpolar(
        r=values,
        theta=categories,
        fill="toself",
        fillcolor="rgba(79,142,247,0.2)",
        line=dict(color="#4F8EF7", width=2),
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        height=320,
        margin=dict(l=20, r=20, t=30, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_star_chart(session_log: list):
    """Donut chart showing STAR method compliance on behavioral questions."""
    answered = [item for item in session_log if not item.get("skipped")]
    behavioral = [i for i in answered if i.get("star_check", {}).get("applicable")]

    if not behavioral:
        st.caption("No behavioral questions were asked in this session.")
        return

    used = sum(1 for i in behavioral if i.get("star_check", {}).get("used_star"))
    not_used = len(behavioral) - used

    fig = go.Figure(go.Pie(
        labels=["STAR Used ✅", "STAR Incomplete ⚠️"],
        values=[used, not_used],
        hole=0.55,
        marker=dict(colors=["#34C98A", "#F76F6F"]),
        textinfo="label+percent",
    ))
    fig.update_layout(
        height=320,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)
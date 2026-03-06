"""
modules/charts.py
All Plotly chart builders for the final report dashboard.
"""

import plotly.graph_objects as go

# ── Colour palette (matches app CSS) ─────────────────────────────────────────
TEAL   = "#00E5CC"
RED    = "#FF6B6B"
AMBER  = "#FFB347"
BG     = "rgba(0,0,0,0)"
GRID   = "#1E2433"
TEXT   = "#E8EAF0"


def _base_layout(**overrides) -> dict:
    layout = dict(
        paper_bgcolor=BG,
        plot_bgcolor=BG,
        font=dict(color=TEXT, family="DM Mono, monospace", size=12),
        margin=dict(l=20, r=20, t=40, b=20),
        height=300,
    )
    layout.update(overrides)
    return layout


# ── 1. Score + Confidence dual-line timeline ──────────────────────────────────

def score_timeline_chart(scores: list, confidence_scores: list) -> go.Figure:
    x = list(range(1, len(scores) + 1))
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=x, y=scores,
        mode="lines+markers",
        name="Score /10",
        line=dict(color=TEAL, width=2),
        marker=dict(size=7),
        yaxis="y1",
    ))

    if confidence_scores:
        fig.add_trace(go.Scatter(
            x=x, y=confidence_scores,
            mode="lines+markers",
            name="Confidence %",
            line=dict(color=AMBER, width=2, dash="dot"),
            marker=dict(size=7),
            yaxis="y2",
        ))

    fig.update_layout(
        **_base_layout(title="Score & Confidence Over Time"),
        xaxis=dict(title="Question #", gridcolor=GRID, tickmode="linear"),
        yaxis=dict(title="Score", range=[0, 10], gridcolor=GRID),
        yaxis2=dict(title="Confidence %", range=[0, 100],
                    overlaying="y", side="right", gridcolor=GRID, showgrid=False),
        legend=dict(orientation="h", y=1.12),
    )
    return fig


# ── 2. Radar / Spider chart ───────────────────────────────────────────────────

def radar_chart(avg_dims: dict) -> go.Figure:
    categories = list(avg_dims.keys())
    values     = [avg_dims[c] * 10 for c in categories]   # scale 1-10 → 10-100

    # Close the polygon
    categories_closed = categories + [categories[0]]
    values_closed     = values + [values[0]]

    fig = go.Figure(go.Scatterpolar(
        r=values_closed,
        theta=categories_closed,
        fill="toself",
        fillcolor=f"rgba(0,229,204,0.15)",
        line=dict(color=TEAL, width=2),
        marker=dict(size=6),
    ))
    fig.update_layout(
        **_base_layout(title="Competency Radar", height=320),
        polar=dict(
            bgcolor=BG,
            radialaxis=dict(visible=True, range=[0, 100],
                            gridcolor=GRID, tickfont=dict(color=TEXT, size=10)),
            angularaxis=dict(gridcolor=GRID),
        ),
    )
    return fig


# ── 3. Per-question score bar ─────────────────────────────────────────────────

def per_question_bar(scores: list) -> go.Figure:
    x      = [f"Q{i+1}" for i in range(len(scores))]
    colors = [
        TEAL  if s >= 7 else
        AMBER if s >= 5 else
        RED
        for s in scores
    ]
    fig = go.Figure(go.Bar(
        x=x, y=scores,
        marker_color=colors,
        text=[str(s) for s in scores],
        textposition="outside",
    ))
    fig.update_layout(
        **_base_layout(title="Score Per Question"),
        xaxis=dict(gridcolor=GRID),
        yaxis=dict(range=[0, 11], gridcolor=GRID),
    )
    return fig


# ── 4. Answer time bar ────────────────────────────────────────────────────────

def answer_time_chart(answer_times: list) -> go.Figure:
    x = [f"Q{i+1}" for i in range(len(answer_times))]
    fig = go.Figure(go.Bar(
        x=x, y=answer_times,
        marker_color="#4F8EF7",
        text=[f"{t}s" for t in answer_times],
        textposition="outside",
    ))
    avg = sum(answer_times) / len(answer_times) if answer_times else 0
    fig.add_hline(y=avg, line_dash="dot", line_color=AMBER,
                  annotation_text=f"Avg {avg:.0f}s", annotation_font_color=AMBER)
    fig.update_layout(
        **_base_layout(title="Answer Time Per Question (seconds)"),
        xaxis=dict(gridcolor=GRID),
        yaxis=dict(gridcolor=GRID),
    )
    return fig


# ── 5. STAR method donut ──────────────────────────────────────────────────────

def star_donut_chart(star_results: list):
    """
    star_results = list of {"applicable": bool, "used_star": bool|None, "missing": [...]}
    Returns None if there are no behavioural questions.
    """
    applicable = [r for r in star_results if r.get("applicable")]
    if not applicable:
        return None

    used     = sum(1 for r in applicable if r.get("used_star") is True)
    not_used = len(applicable) - used

    fig = go.Figure(go.Pie(
        labels=["STAR Used ✅", "STAR Incomplete ⚠️"],
        values=[used, not_used],
        hole=0.6,
        marker=dict(colors=[TEAL, RED]),
        textinfo="label+percent",
        textfont=dict(color=TEXT),
    ))
    fig.update_layout(
        **_base_layout(title="STAR Method Compliance", height=320),
        showlegend=False,
    )
    return fig
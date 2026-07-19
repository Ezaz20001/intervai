import plotly.graph_objects as go
import numpy as np


def create_radar_chart(categories: list, values: list, title: str = "Skill Radar") -> go.Figure:
    if not categories or not values:
        return go.Figure()

    num_vars = len(categories)
    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
    values_plot = values + [values[0]]
    angles += [angles[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values_plot,
        theta=angles,
        fill="toself",
        fillcolor="rgba(99,102,241,0.2)",
        line=dict(color="#6366F1", width=2),
        marker=dict(size=8, color="#8B5CF6"),
        name="Score",
    ))

    fig.update_layout(
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(
                visible=True,
                range=[0, 10],
                showticklabels=True,
                tickfont=dict(color="#c7c4d7", size=10),
                gridcolor="rgba(255,255,255,0.08)",
                linecolor="rgba(255,255,255,0.05)",
            ),
            angularaxis=dict(
                tickfont=dict(color="#e0e3e5", size=11, family="Inter, sans-serif"),
                gridcolor="rgba(255,255,255,0.08)",
                linecolor="rgba(255,255,255,0.05)",
            ),
        ),
        showlegend=False,
        title=dict(
            text=title,
            font=dict(color="#e0e3e5", size=14, family="Inter, sans-serif"),
            x=0.5,
        ),
        height=300,
        margin=dict(l=40, r=40, t=50, b=30),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )

    return fig


def create_session_radar(session_data: dict) -> go.Figure:
    categories = []
    values = []

    category_map = {
        "star_score": "STAR Format",
        "coherence_score": "Coherence",
        "keyword_score": "Keywords",
    }

    for key, label in category_map.items():
        if key in session_data and session_data[key] > 0:
            categories.append(label)
            values.append(session_data[key])

    if not categories:
        categories = ["No Data"]
        values = [0]

    return create_radar_chart(categories, values, "Answer Quality Breakdown")
